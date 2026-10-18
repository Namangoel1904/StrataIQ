"""
StrataIQ Backend Configuration
Dual-engine: SQLite (local dev) or Cloud SQL PostgreSQL (production via DATABASE_URL env var)
"""
import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(_env_path)
except Exception:
    pass


class Settings:
    """Central application settings — reads from environment variables."""

    # If set, overrides SQLite and uses PostgreSQL (Cloud SQL / AlloyDB)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Gemini API — Phase 2 agents use this. Falls back to deterministic mode if empty.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Model names — configurable via env for easy swap between flash/pro
    GEMINI_FLASH_MODEL: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
    GEMINI_PRO_MODEL: str = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    # Tinker LoRA Router SDK key & models (Gemma 4 Only)
    TINKER_API_KEY: str = os.getenv("TINKER_API_KEY", "")
    TINKER_BASE_MODEL: str = os.getenv("TINKER_BASE_MODEL", "google/gemma-4-e4b-it")
    GOOGLE_GEMMA_ROUTER_MODEL: str = os.getenv("GOOGLE_GEMMA_ROUTER_MODEL", "gemma-4-e4b-it")

    # Backboard.io persistent user memory SDK key
    BACKBOARD_API_KEY: str = os.getenv("BACKBOARD_API_KEY", "")

    # Google Cloud Project ID for Cloud Run / Firestore
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", os.getenv("GCP_PROJECT", ""))

    def __init__(self) -> None:
        # Automatically mirror GEMINI_API_KEY to GOOGLE_API_KEY for google-adk
        if self.GEMINI_API_KEY and not os.environ.get("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = self.GEMINI_API_KEY

    # Absolute path to the local SQLite replica
    SQLITE_DB_PATH: Path = (
        Path(__file__).parent.parent.parent
        / "enterprise_data_vault"
        / "rdbms"
        / "local_enterprise.db"
    )

    # Absolute path to the enterprise files directory
    FILES_DIR: Path = (
        Path(__file__).parent.parent.parent
        / "enterprise_data_vault"
        / "files"
    )

    @property
    def effective_db_url(self) -> str:
        """Return Postgres URL if DATABASE_URL is set, else SQLite URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite:///{self.SQLITE_DB_PATH.as_posix()}"

    @property
    def is_sqlite(self) -> bool:
        return not bool(self.DATABASE_URL)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
