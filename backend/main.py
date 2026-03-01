import os
import json
import uuid
import shutil
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import jwt
import requests
from datetime import datetime, timedelta

app = FastAPI(title="Emily Portfolio Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment bindings
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "emily123")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-prod")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = "github.com/blakeaa827/emily-portfolio.git"
REPO_DIR = Path("/tmp/portfolio-repo")

# -----------------
# Security Middleware
# -----------------
class AuthRequest(BaseModel):
    password: str

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -----------------
# Git Subsystem
# -----------------
def init_repo():
    if not GITHUB_TOKEN:
        print("WARNING: No GITHUB_TOKEN set. Git pushing will fail.")
        
    if REPO_DIR.exists():
        shutil.rmtree(REPO_DIR)
        
    auth_url = f"https://oauth2:{GITHUB_TOKEN}@{GITHUB_REPO}"
    
    # Clone Repo
    subprocess.run(["git", "clone", auth_url, str(REPO_DIR)], check=True)
    
    # Configure Git
    subprocess.run(["git", "config", "user.email", "copilot@antigravity.sys"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "config", "user.name", "On-Page Copilot"], cwd=REPO_DIR, check=True)

@app.on_event("startup")
async def startup_event():
    # 1. Unpack Gemini Auth Credentials
    paths_to_populate = [Path.home() / ".gemini", Path("/root/.gemini")]
    
    for gemini_home in paths_to_populate:
        try:
            gemini_home.mkdir(parents=True, exist_ok=True)
            if "GEMINI_OAUTH_CREDS_JSON" in os.environ:
                (gemini_home / "oauth_creds.json").write_text(os.environ["GEMINI_OAUTH_CREDS_JSON"])
            if "GEMINI_SETTINGS_JSON" in os.environ:
                (gemini_home / "settings.json").write_text(os.environ["GEMINI_SETTINGS_JSON"])
            print(f"Injected credentials into {gemini_home}")
        except Exception as e:
            print(f"Skipped {gemini_home}: {e}")

    # 2. Setup GitHub Repo and Static Route
    init_repo()

# Mount the live preview directory
app.mount("/live-preview", StaticFiles(directory=str(REPO_DIR / "dist"), html=True), name="live-preview")

# -----------------
# Gemini Client
# -----------------
class PreviewRequest(BaseModel):
    prompt: str

@app.post("/api/preview")
async def preview_changes(req: PreviewRequest, _=Depends(verify_token)):
    app_jsx_path = REPO_DIR / "src" / "App.jsx"
    
    if not app_jsx_path.exists():
        raise HTTPException(status_code=500, detail="Repo missing")

    current_code = app_jsx_path.read_text()
    
    async def event_generator():
        yield f"data: {json.dumps({'status': 'Architecting UI structure...'})}\n\n"
        
        system_prompt = f"""You are a World-Class Senior Creative Technologist.
You are modifying an existing React portfolio (App.jsx) based on the user's latest prompt.
Return ONLY valid, highly structured React JSX code. 
Do not wrap it in markdown block quotes (e.g. ```jsx). 
No yapping. Only the exact raw source string.

CURRENT SOURCE:
{current_code}
"""
        yield f"data: {json.dumps({'status': 'Querying Gemini 2.0 Pro Inference Engine...'})}\n\n"
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            yield f"data: {json.dumps({'error': 'GEMINI_API_KEY is not set in the environment.'})}\n\n"
            return
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"
        
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": req.prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        # We use sync requests here for simplicity within the async generator, 
        # or we could use httpx. For now, requests.post is perfectly fine.
        loop = asyncio.get_event_loop()
        try:
            resp = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, headers={'Content-Type': 'application/json'}))
            resp.raise_for_status()
            data = resp.json()
            
            raw_response = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            err_msg = str(e)
            if 'resp' in locals(): err_msg += f" - {resp.text}"
            yield f"data: {json.dumps({'error': f'Gemini API Error: {err_msg}'})}\n\n"
            return
            if raw_response.startswith("```"):
                lines = raw_response.splitlines()
                if lines[0].startswith("```"): lines = lines[1:]
                if lines[-1].startswith("```"): lines = lines[:-1]
                raw_response = "\n".join(lines)
                
            yield f"data: {json.dumps({'status': 'Applying code modifications to App.jsx...'})}\n\n"
            app_jsx_path.write_text(raw_response)
            
            yield f"data: {json.dumps({'status': 'Compiling native Vite application payload...'})}\n\n"
            
            # Build the dynamic preview
            build_proc = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=REPO_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await build_proc.communicate()
            
            if build_proc.returncode != 0:
                subprocess.run(["git", "checkout", "src/App.jsx"], cwd=REPO_DIR)
                yield f"data: {json.dumps({'error': 'Webpack build failed on generated code.'})}\n\n"
                return
                
            yield f"data: {json.dumps({'status': 'Complete.', 'previewUrl': '/live-preview/'})}\n\n"
            
        except Exception as e:
            subprocess.run(["git", "checkout", "src/App.jsx"], cwd=REPO_DIR)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/publish")
async def publish_changes(_=Depends(verify_token)):
    app_jsx_path = REPO_DIR / "src" / "App.jsx"
    
    # Commit and Push the dirty active preview
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    try:
        subprocess.run(["git", "add", "src/App.jsx"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", f"Automated Copilot Update [{ts}]"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
        return {"success": True}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git push failed: {e}")

@app.post("/api/revert")
async def revert_changes(_=Depends(verify_token)):
    try:
        subprocess.run(["git", "fetch", "origin"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=REPO_DIR, check=True)
        
        # Build to reset the preview environment
        subprocess.run(["npm", "run", "build"], cwd=REPO_DIR, check=True)
        
        return {"success": True, "message": "Successfully reverted the last preview."}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git revert failed: {e}")
