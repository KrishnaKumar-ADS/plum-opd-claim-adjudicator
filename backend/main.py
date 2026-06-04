"""FastAPI application entrypoint."""

import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import get_settings
from backend.database import init_db
from backend.utils.logger import get_logger

logger = get_logger("main")
settings = get_settings()

# Detect if built frontend is available (Docker / HF Spaces deployment)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend_static"
SERVE_FRONTEND = FRONTEND_DIR.is_dir()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting Plum OPD Claim Adjudicator...")

    # Create required directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.data_dir, "claims"), exist_ok=True)

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Initialize vector store (ingest policy documents)
    if not os.environ.get("VERCEL"):
        try:
            from backend.ai.rag.ingest import ingest_policy_documents
            ingest_policy_documents()
            logger.info("Vector store ready")
        except Exception as e:
            logger.warning(f"Vector store initialization skipped (run 'python scripts/build_vector_store.py' manually): {e}")
    else:
        logger.info("Skipping vector store ingestion on Vercel (running in serverless mode)")

    if SERVE_FRONTEND:
        logger.info(f"Serving frontend from {FRONTEND_DIR}")
    else:
        logger.info("No frontend_static directory found; running API-only mode")

    logger.info("Application started successfully!")
    yield

    # Shutdown
    logger.info("Shutting down...")
    from backend.ai.gemini_client import get_ai_client
    get_ai_client().close()


app = FastAPI(
    title="Plum OPD Claim Adjudicator",
    description="AI-powered OPD insurance claim adjudication system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from backend.api.claims import router as claims_router
from backend.api.decisions import router as decisions_router
from backend.api.appeals import router as appeals_router
from backend.api.admin import router as admin_router
from backend.api.evaluation import router as eval_router

app.include_router(claims_router)
app.include_router(decisions_router)
app.include_router(appeals_router)
app.include_router(admin_router)
app.include_router(eval_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ── Serve React frontend (only in Docker / HF Spaces) ────────────────────
if SERVE_FRONTEND:
    # Mount static assets (JS, CSS, images) under /assets
    assets_dir = FRONTEND_DIR / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    # Serve favicon and other root-level static files
    @app.get("/favicon.svg")
    @app.get("/favicon.ico")
    async def favicon():
        for name in ["favicon.svg", "favicon.ico"]:
            fpath = FRONTEND_DIR / name
            if fpath.exists():
                return FileResponse(str(fpath))
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    # Catch-all: serve index.html for SPA client-side routing
    # This MUST be last so API routes take priority
    @app.get("/{rest_of_path:path}")
    async def serve_react_app(rest_of_path: str):
        # If the path points to an actual file in frontend_static, serve it
        file_path = FRONTEND_DIR / rest_of_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for React Router
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "name": "Plum OPD Claim Adjudicator",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        }
