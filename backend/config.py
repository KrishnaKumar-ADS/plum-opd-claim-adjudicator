"""Application configuration and environment loading."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AI Provider Keys
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    mistral_api_key: str = ""

    # Model Configuration
    groq_model: str = "llama-3.3-70b-versatile"
    openrouter_vision_model: str = "google/gemini-2.5-flash-preview-05-20"
    mistral_model: str = "mistral-small-latest"

    # Database
    database_url: str = "sqlite:////tmp/claims.db" if os.environ.get("VERCEL") or os.environ.get("SPACE_ID") else "sqlite:///./data/claims.db"

    # Vector Store
    chroma_persist_dir: str = "/tmp/vector_store" if os.environ.get("VERCEL") or os.environ.get("SPACE_ID") else "./data/vector_store"

    # Application
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    upload_dir: str = "/tmp/claims/uploads" if os.environ.get("VERCEL") or os.environ.get("SPACE_ID") else "./data/claims/uploads"
    max_file_size_mb: int = 10

    # Paths
    base_dir: str = str(Path(__file__).resolve().parent.parent)
    data_dir: str = "/tmp" if os.environ.get("VERCEL") else str(Path(__file__).resolve().parent.parent / "data")
    prompts_dir: str = str(Path(__file__).resolve().parent.parent / "prompts")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def policy_terms_path(self) -> Path:
        return Path(self.base_dir) / "data" / "policies" / "policy_terms.json"

    @property
    def adjudication_rules_path(self) -> Path:
        return Path(self.base_dir) / "data" / "rules" / "adjudication_rules.md"

    @property
    def test_cases_path(self) -> Path:
        return Path(self.base_dir) / "data" / "evaluations" / "test_cases.json"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_policy_config() -> dict:
    """Load policy configuration from file, or return default values."""
    import json
    from pathlib import Path
    settings = get_settings()
    config_path = Path(settings.data_dir) / "config" / "policy_config.json"
    
    default_config = {
        "per_claim_limit": 5000,
        "annual_limit": 50000,
        "copay_percentage": 20,
        "confidence_threshold_manual": 0.70,
        "fraud_risk_threshold": 0.6,
        "max_medicines_per_claim": 10,
        "consultation_fee_limit": 1500,
        "diagnostic_tests_limit": 3000,
        "specialist_fee_limit": 2500,
        "network_discount_percentage": 10,
        "waiting_period_days": 30,
        "cashless_claim_limit": 10000,
    }
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Merge with defaults
            default_config.update(saved)
        except Exception:
            pass
            
    return default_config

