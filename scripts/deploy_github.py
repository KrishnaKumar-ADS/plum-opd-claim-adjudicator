import json
import urllib.request
import urllib.error
import subprocess
import os
from pathlib import Path

token = "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"
repo_name = "plum-opd-claim-adjudicator"

def get_github_username(token):
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Plum-Deploy-Agent"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data["login"]
    except Exception as e:
        print(f"Error fetching user details: {e}")
        raise

def create_github_repo(token, repo_name):
    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=json.dumps({"name": repo_name, "private": True, "description": "Plum OPD Claim Adjudicator"}).encode(),
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "User-Agent": "Plum-Deploy-Agent"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"Repository created: {data['html_url']}")
            return data["html_url"]
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print("Repository already exists on GitHub. Proceeding with existing repository.")
            return None
        else:
            print(f"Failed to create repository: {e.read().decode()}")
            raise
    except Exception as e:
        print(f"Error creating repository: {e}")
        raise

def run_git_commands(username, token, repo_name):
    commands = [
        ["git", "init"],
        ["git", "config", "user.name", "Plum Deployer"],
        ["git", "config", "user.email", "deploy@plum.com"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Initial commit - ready for Vercel deployment"],
        ["git", "branch", "-M", "main"]
    ]
    
    # Run from the project root directory
    project_root = str(Path(__file__).resolve().parent.parent)
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        res = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        if res.returncode != 0:
            print(f"Warning/Message: {res.stderr.strip() or res.stdout.strip()}")
            
    # Add remote with credentials embedded
    remote_url = f"https://{token}@github.com/{username}/{repo_name}.git"
    print("Setting remote origin...")
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True, cwd=project_root) # remove if exists
    res = subprocess.run(["git", "remote", "add", "origin", remote_url], capture_output=True, text=True, cwd=project_root)
    if res.returncode != 0:
        print(f"Failed to add remote: {res.stderr}")
        
    print("Pushing to GitHub main branch (force)...")
    res = subprocess.run(["git", "push", "-u", "origin", "main", "-f"], capture_output=True, text=True, cwd=project_root)
    if res.returncode == 0:
        print("\n🎉 Successfully pushed to GitHub!")
        print(f"Repository URL: https://github.com/{username}/{repo_name}")
    else:
        print(f"Push failed: {res.stderr}")
        raise RuntimeError("Push failed")

if __name__ == "__main__":
    try:
        username = get_github_username(token)
        print(f"Authenticated as GitHub user: {username}")
        create_github_repo(token, repo_name)
        run_git_commands(username, token, repo_name)
    except Exception as e:
        print(f"Deployment failed: {e}")
