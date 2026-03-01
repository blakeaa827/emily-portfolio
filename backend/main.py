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

# Gemini CLI OAuth client credentials (loaded from Render env vars)
GEMINI_CLIENT_ID = os.getenv("GEMINI_CLIENT_ID", "")
GEMINI_CLIENT_SECRET = os.getenv("GEMINI_CLIENT_SECRET", "")

# Code Assist API endpoint (from @google/gemini-cli-core/dist/src/code_assist/server.js)
CODE_ASSIST_BASE = "https://cloudcode-pa.googleapis.com/v1internal"

# Cached project ID (populated on first use)
_cached_project_id = None

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
    
    auth_url = f"https://oauth2:{GITHUB_TOKEN}@{GITHUB_REPO}"
    
    if REPO_DIR.exists() and (REPO_DIR / ".git").exists():
        # Repo was pre-cached during Docker build — preserve node_modules and dist
        # Just re-auth the remote and pull latest
        print("Using pre-cached repo, updating remote and pulling latest...")
        subprocess.run(["git", "remote", "set-url", "origin", auth_url], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "fetch", "origin"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=REPO_DIR, check=True)
    else:
        # No cached repo — full clone
        if REPO_DIR.exists():
            shutil.rmtree(REPO_DIR)
        print("Cloning fresh repo...")
        subprocess.run(["git", "clone", auth_url, str(REPO_DIR)], check=True)
        # Install dependencies since there's no cache
        subprocess.run(["npm", "install"], cwd=REPO_DIR, check=True)
        subprocess.run(["npm", "run", "build"], cwd=REPO_DIR, check=True)
    
    # Configure Git identity
    subprocess.run(["git", "config", "user.email", "copilot@antigravity.sys"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "config", "user.name", "On-Page Copilot"], cwd=REPO_DIR, check=True)

# -----------------
# OAuth + Code Assist Client
# -----------------
def get_gemini_access_token():
    """Use the refresh_token from the user's Google One AI Premium subscription
    to mint a fresh access_token for the Code Assist API."""
    oauth_json_str = os.environ.get("GEMINI_OAUTH_CREDS_JSON")
    if not oauth_json_str:
        raise Exception("GEMINI_OAUTH_CREDS_JSON is not set.")
    
    oauth_creds = json.loads(oauth_json_str)
    refresh_token = oauth_creds.get("refresh_token")
    
    if not refresh_token:
        raise Exception("No refresh_token found in OAuth credentials.")
    
    token_resp = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GEMINI_CLIENT_ID,
        "client_secret": GEMINI_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    })
    token_resp.raise_for_status()
    return token_resp.json()["access_token"]


def get_code_assist_project(access_token: str) -> str:
    """Calls loadCodeAssist to retrieve the user's cloudaicompanionProject ID."""
    global _cached_project_id
    if _cached_project_id:
        return _cached_project_id
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    resp = requests.post(f"{CODE_ASSIST_BASE}:loadCodeAssist", 
        json={
            "metadata": {
                "ideType": "IDE_UNSPECIFIED",
                "platform": "PLATFORM_UNSPECIFIED",
                "pluginType": "GEMINI"
            }
        },
        headers=headers
    )
    resp.raise_for_status()
    project = resp.json().get("cloudaicompanionProject")
    if not project:
        raise Exception("No cloudaicompanionProject returned from loadCodeAssist")
    
    _cached_project_id = project
    return project


def call_gemini(access_token: str, project_id: str, system_prompt: str, user_prompt: str) -> str:
    """Calls the Code Assist generateContent endpoint and returns the model's text output."""
    session_id = str(uuid.uuid4())
    
    payload = {
        "model": "gemini-2.5-pro",
        "project": project_id,
        "user_prompt_id": str(uuid.uuid4()),
        "request": {
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "systemInstruction": {
                "role": "user",
                "parts": [{"text": system_prompt}]
            },
            "generationConfig": {"temperature": 0.2},
            "session_id": session_id
        }
    }
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    resp = requests.post(f"{CODE_ASSIST_BASE}:generateContent", json=payload, headers=headers, timeout=120)
    resp.raise_for_status()
    
    data = resp.json()
    return data.get("response", {}).get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")


@app.on_event("startup")
async def startup_event():
    # Setup GitHub Repo (preserves Docker-cached node_modules + dist)
    init_repo()
    # Mount the live preview directory AFTER the repo is ready
    app.mount("/live-preview", StaticFiles(directory=str(REPO_DIR / "dist"), html=True), name="live-preview")

# -----------------
# Auth Endpoint
# -----------------
@app.post("/api/auth")
async def login(request: AuthRequest):
    if request.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = jwt.encode(
        {"sub": "admin", "exp": datetime.utcnow() + timedelta(hours=12)},
        JWT_SECRET,
        algorithm="HS256"
    )
    return {"token": token}

# -----------------
# Preview Endpoint (SSE)
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
        yield 'data: {"status": "Architecting UI structure..."}\n\n'
        
        system_prompt = (
            "You are a World-Class Senior Creative Technologist.\n"
            "You are modifying an existing React portfolio (App.jsx) based on the user's latest prompt.\n"
            "Return ONLY valid, highly structured React JSX code.\n"
            "Do not wrap it in markdown block quotes (e.g. ```jsx).\n"
            "No yapping. Only the exact raw source string.\n\n"
            "CURRENT SOURCE:\n" + current_code
        )
        
        yield 'data: {"status": "Authenticating with Gemini Code Assist..."}\n\n'
        
        # Mint fresh OAuth access token
        try:
            access_token = get_gemini_access_token()
        except Exception as e:
            yield f'data: {json.dumps({"error": f"OAuth Error: {str(e)}"})}\n\n'
            return
        
        yield 'data: {"status": "Resolving project context..."}\n\n'
        
        # Get project ID
        try:
            project_id = get_code_assist_project(access_token)
        except Exception as e:
            yield f'data: {json.dumps({"error": f"Project Error: {str(e)}"})}\n\n'
            return
        
        yield 'data: {"status": "Querying Gemini 2.5 Pro Inference Engine..."}\n\n'
        
        # Call Code Assist generateContent
        loop = asyncio.get_event_loop()
        try:
            raw_response = await loop.run_in_executor(
                None,
                lambda: call_gemini(access_token, project_id, system_prompt, req.prompt)
            )
        except Exception as e:
            err_msg = str(e)
            yield f'data: {json.dumps({"error": f"Gemini Error: {err_msg}"})}\n\n'
            return
        
        # Strip markdown code fences if the model wrapped the output
        if raw_response.startswith("```"):
            lines = raw_response.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_response = "\n".join(lines)
        
        try:
            yield 'data: {"status": "Applying code modifications to App.jsx..."}\n\n'
            app_jsx_path.write_text(raw_response)
            
            yield 'data: {"status": "Compiling native Vite application payload..."}\n\n'
            
            build_proc = await asyncio.create_subprocess_exec(
                "npm", "run", "build",
                cwd=REPO_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            await build_proc.communicate()
            
            if build_proc.returncode != 0:
                subprocess.run(["git", "checkout", "src/App.jsx"], cwd=REPO_DIR)
                yield 'data: {"error": "Vite build failed on generated code."}\n\n'
                return
            
            yield f'data: {json.dumps({"status": "Complete.", "previewUrl": "/live-preview/"})}\n\n'
        except Exception as e:
            subprocess.run(["git", "checkout", "src/App.jsx"], cwd=REPO_DIR)
            yield f'data: {json.dumps({"error": str(e)})}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# -----------------
# Publish & Revert
# -----------------
@app.post("/api/publish")
async def publish_changes(_=Depends(verify_token)):
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
        subprocess.run(["npm", "run", "build"], cwd=REPO_DIR, check=True)
        return {"success": True, "message": "Successfully reverted the last preview."}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git revert failed: {e}")
