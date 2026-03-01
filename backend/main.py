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
from pydantic import BaseModel
import jwt
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
    gemini_home = Path.home() / ".gemini"
    gemini_home.mkdir(parents=True, exist_ok=True)
    
    if "GEMINI_OAUTH_CREDS_JSON" in os.environ:
        (gemini_home / "oauth_creds.json").write_text(os.environ["GEMINI_OAUTH_CREDS_JSON"])
        print("Successfully injected GEMINI_OAUTH_CREDS_JSON into container.")
    
    if "GEMINI_SETTINGS_JSON" in os.environ:
        (gemini_home / "settings.json").write_text(os.environ["GEMINI_SETTINGS_JSON"])
        print("Successfully injected GEMINI_SETTINGS_JSON into container.")

    # 2. Setup GitHub Repo
    init_repo()

# -----------------
# Gemini Client
# -----------------
class GeminiClient:
    async def generate_code(self, prompt: str, current_code: str) -> str:
        # Reconstruct the soul.md logic
        system_prompt = f"""You are a World-Class Senior Creative Technologist.
You are modifying an existing React portfolio (App.jsx) based on the user's latest prompt.
Return ONLY valid, highly structured React JSX code. 
Do not wrap it in markdown block quotes (e.g. ```jsx). 
No yapping. Only the exact raw source string.

CURRENT SOURCE:
{current_code}
"""
        env = os.environ.copy()
        
        # Write system prompt to tmp
        tmp_sys = Path(f"/tmp/sys_{uuid.uuid4()}.md")
        tmp_sys.write_text(system_prompt)
        env["GEMINI_SYSTEM_MD"] = str(tmp_sys)
        
        cmd = [
            "gemini", 
            "query",
            "-", 
            "--output-format", "json"
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        stdout, stderr = await proc.communicate(input=prompt.encode())
        
        if proc.returncode != 0:
            raise Exception(f"Gemini Error: {stderr.decode()}")
            
        try:
            data = json.loads(stdout.decode().strip())
            raw_response = data.get("response", "")
            # Clear markdown fences if the model forgot
            if raw_response.startswith("```"):
                lines = raw_response.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_response = "\n".join(lines)
            return raw_response
        except Exception as e:
            raise Exception(f"Failed to parse model output: {e}")

# -----------------
# API Endpoints
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

class PreviewRequest(BaseModel):
    prompt: str

@app.post("/api/preview")
async def preview_changes(req: PreviewRequest, _=Depends(verify_token)):
    app_jsx_path = REPO_DIR / "src" / "App.jsx"
    
    if not app_jsx_path.exists():
        # Fallback if local repo clone failed
        return {"error": "Local git repository not initialized correctly."}
        
    current_code = app_jsx_path.read_text()
    
    client = GeminiClient()
    try:
        new_code = await client.generate_code(req.prompt, current_code)
        return {"code": new_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PublishRequest(BaseModel):
    code: str

@app.post("/api/publish")
async def publish_changes(req: PublishRequest, _=Depends(verify_token)):
    app_jsx_path = REPO_DIR / "src" / "App.jsx"
    
    # Verify working tree is clean before starting
    subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "pull", "origin", "main"], cwd=REPO_DIR, check=True)
    
    # Overwrite
    app_jsx_path.write_text(req.code)
    
    # Commit and Push
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
        # Revert HEAD
        subprocess.run(["git", "revert", "--no-edit", "HEAD"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
        return {"success": True, "message": "Successfully reverted the last commit."}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git revert failed: {e}")
