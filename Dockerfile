# ──────────────────────────────────────────────────────────────────────────
# Plum OPD Claim Adjudicator – Backend Dockerfile
# ──────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# System deps (for pypdf2, chromadb, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd -m -u 1000 appuser

WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy application source ───────────────────────────────────────────────
COPY backend/ ./backend/
COPY prompts/ ./prompts/
COPY data/ ./data/

# Create writable directories that the app needs at runtime
RUN mkdir -p data/claims/uploads data/vector_store data/config \
    && chown -R appuser:appuser /app

USER appuser

# ── Runtime config ────────────────────────────────────────────────────────
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8001

EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# ── Entry point ───────────────────────────────────────────────────────────
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]
