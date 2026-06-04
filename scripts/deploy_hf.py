"""
Deploy Plum OPD Claim Adjudicator to Hugging Face Spaces.

Usage:
    python scripts/deploy_hf.py

Requires:
    pip install huggingface_hub
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────
HF_TOKEN = os.environ.get("HF_TOKEN", "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")
HF_USERNAME = None  # Auto-detected from token
SPACE_NAME = "plum-opd-claim-adjudicator"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files/dirs to include in the Space
INCLUDE_DIRS = ["backend", "prompts", "data/policies", "data/rules", "data/evaluations", "frontend"]
INCLUDE_FILES = ["requirements.txt"]


def main():
    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("❌ huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    api = HfApi(token=HF_TOKEN)

    # Detect username
    user_info = api.whoami()
    username = user_info["name"]
    repo_id = f"{username}/{SPACE_NAME}"
    print(f"📦 Deploying to: https://huggingface.co/spaces/{repo_id}")

    # ── 1. Create or update the Space ────────────────────────────────────
    try:
        api.create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="docker",
            private=False,
            exist_ok=True,
        )
        print(f"✅ Space '{repo_id}' ready")
    except Exception as e:
        print(f"⚠️  Space creation note: {e}")

    # ── 2. Add secrets for API keys ──────────────────────────────────────
    env_path = PROJECT_ROOT / ".env"
    secrets = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if key in ("GROQ_API_KEY", "OPENROUTER_API_KEY", "MISTRAL_API_KEY"):
                        secrets[key] = value

    for key, value in secrets.items():
        try:
            api.add_space_secret(repo_id=repo_id, key=key, value=value)
            print(f"🔑 Secret '{key}' set")
        except Exception as e:
            print(f"⚠️  Could not set secret '{key}': {e}")

    # ── 3. Prepare upload directory ──────────────────────────────────────
    staging = Path(tempfile.mkdtemp(prefix="hf_deploy_"))
    print(f"📁 Staging directory: {staging}")

    try:
        # Copy Dockerfile.hf as Dockerfile (HF Spaces requires it at root)
        dockerfile_src = PROJECT_ROOT / "Dockerfile.hf"
        shutil.copy2(dockerfile_src, staging / "Dockerfile")
        print("  ✓ Dockerfile")

        # Copy requirements.txt
        for f in INCLUDE_FILES:
            src = PROJECT_ROOT / f
            if src.exists():
                shutil.copy2(src, staging / f)
                print(f"  ✓ {f}")

        # Copy directories
        for d in INCLUDE_DIRS:
            src = PROJECT_ROOT / d
            dst = staging / d
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "node_modules", "dist", ".git",
                    "*.db", "*.db-wal", "*.db-shm", "*.db-journal",
                    "vector_store", "vector_store_test", "uploads"
                ))
                print(f"  ✓ {d}/")
            else:
                print(f"  ⚠️ Skipped {d}/ (not found)")

        # Create a README.md for the Space (HF metadata)
        readme_content = f"""---
title: Plum OPD Claim Adjudicator
emoji: 🏥
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: AI-powered OPD insurance claim adjudication system
---

# 🏥 Plum OPD Claim Adjudicator

AI-powered OPD insurance claim adjudication system with multi-provider LLM support.

## Features
- **Automated Claim Processing** — Submit and adjudicate OPD claims instantly
- **Multi-Stage Decision Engine** — Eligibility, coverage, limits, and medical necessity checks
- **RAG-Enhanced Policy Lookup** — Retrieval-augmented generation for accurate policy matching
- **Fraud Detection** — AI-powered suspicious claim flagging
- **Appeal Management** — Full appeal workflow with AI-assisted review
- **Real-time Dashboard** — Monitor claims, decisions, and performance metrics

## Tech Stack
- **Backend:** FastAPI + SQLAlchemy + ChromaDB
- **Frontend:** React + Vite
- **AI Providers:** Groq (Llama 3.3), OpenRouter (Gemini), Mistral
"""
        with open(staging / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        print("  ✓ README.md (Space metadata)")

        # ── 4. Upload everything to HF Space ────────────────────────────
        print("\n🚀 Uploading to Hugging Face Spaces...")
        api.upload_folder(
            folder_path=str(staging),
            repo_id=repo_id,
            repo_type="space",
            commit_message="Deploy Plum OPD Claim Adjudicator to HF Spaces",
        )
        print(f"\n✅ Deployment complete!")
        print(f"🌐 Your Space: https://huggingface.co/spaces/{repo_id}")
        print(f"⏳ The Docker image is now building. It may take a few minutes to go live.")

    finally:
        # Cleanup staging directory
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    main()
