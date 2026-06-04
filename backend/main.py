"""FastAPI application entrypoint."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import get_settings
from backend.database import init_db
from backend.utils.logger import get_logger

logger = get_logger("main")
settings = get_settings()


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


@app.get("/")
def root():
    return {
        "name": "Plum OPD Claim Adjudicator",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
