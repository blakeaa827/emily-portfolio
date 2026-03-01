import os
import sys
import json
import requests
import uuid
from pathlib import Path

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_URL = "https://github.com/blakeaa827/emily-portfolio"

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def get_gemini_creds():
    creds_path = Path.home() / ".gemini" / "oauth_creds.json"
    settings_path = Path.home() / ".gemini" / "settings.json"
    
    creds = creds_path.read_text() if creds_path.exists() else ""
    settings = settings_path.read_text() if settings_path.exists() else ""
    return creds, settings

def deploy():
    print("1. Reading local Gemini authentication strings...")
    oauth_creds, settings = get_gemini_creds()
    if not oauth_creds:
        print("WARNING: oauth_creds.json not found locally!")

    print("2. Provisioning Web Service on Render...")
    payload = {
        "type": "web_service",
        "name": "emily-portfolio-copilot",
        "repo": REPO_URL,
        "branch": "main",
        "rootDir": "backend",
        "env": "docker",
        "region": "oregon",
        "plan": "free"
    }

    # First attempt to list existing services to see if it's already there
    resp_list = requests.get("https://api.render.com/v1/services", headers=HEADERS)
    service_id = None
    if resp_list.status_code == 200:
        for s in resp_list.json():
            if s.get("service", {}).get("name") == "emily-portfolio-copilot":
                service_id = s["service"]["id"]
                print(f"Service already exists: {service_id}")
                break

    if not service_id:
        resp = requests.post("https://api.render.com/v1/services", headers=HEADERS, json=payload)
        if resp.status_code != 201:
            print(f"Failed to create service: {resp.status_code} - {resp.text}")
            sys.exit(1)
        
        service_id = resp.json()["id"]
        print(f"Created Service: {service_id}")

    print("3. Injecting Environment Variables...")
    
    # Generate random JWT secret
    jwt_secret = str(uuid.uuid4())
    
    env_vars = [
        {"envVar": {"name": "ADMIN_PASSWORD", "value": "emily123"}},
        {"envVar": {"name": "JWT_SECRET", "value": jwt_secret}},
        {"envVar": {"name": "GITHUB_TOKEN", "value": GITHUB_TOKEN}},
        {"envVar": {"name": "GEMINI_OAUTH_CREDS_JSON", "value": oauth_creds}},
        {"envVar": {"name": "GEMINI_SETTINGS_JSON", "value": settings}},
        {"envVar": {"name": "PORT", "value": "10000"}},
    ]
    
    env_resp = requests.put(
        f"https://api.render.com/v1/services/{service_id}/env-vars", 
        headers=HEADERS, 
        json=env_vars
    )
    
    if env_resp.status_code == 200:
        print("✅ Environment Variables successfully injected!")
    else:
        print(f"❌ Failed to set env vars: {env_resp.status_code} - {env_resp.text}")

    print("Deployment triggered successfully. The Copilot Engine is building in the cloud.")

if __name__ == "__main__":
    deploy()
