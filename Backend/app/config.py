import os
from pathlib import Path
from dotenv import load_dotenv



load_dotenv()

# backend/app/config.py -> remonte de 2 niveaux pour arriver à backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_PDF_PATH = RAW_DATA_DIR / "clark_county_hr_manual.pdf"
RAW_SECTIONS_PATH = PROCESSED_DATA_DIR / "raw_sections.json"
CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks.jsonl"

# --- Qdrant ---
# Local (docker-compose) : QDRANT_HOST/QDRANT_PORT suffisent.
# Qdrant Cloud : définir QDRANT_URL (+ QDRANT_API_KEY) ; ça prend le dessus.
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "hr_policy_chunks")

# --- Evaluation ---
EVAL_DIR = PROJECT_ROOT / "eval"
GOLDEN_DATASET_PATH = EVAL_DIR / "golden_dataset" / "hr_questions.json"
EVAL_RESULTS_DIR = EVAL_DIR / "results"

# --- PostgreSQL ---
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "hr_assistant_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "hr_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "hr_password")

# --- Auth / Sécurité ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

_DEV_SECRET = "CHANGE_ME_dev_only_secret_key_replace_before_prod"
SECRET_KEY = os.getenv("SECRET_KEY") or _DEV_SECRET

if ENVIRONMENT == "production" and SECRET_KEY == _DEV_SECRET:
    raise RuntimeError("SECRET_KEY manquante : obligatoire en production.")




JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

# --- Database URL (SQLAlchemy / psycopg2) ---
# Si DATABASE_URL est fournie (cas Neon), elle prend le dessus.
_DATABASE_URL_ENV = os.getenv("DATABASE_URL")

if _DATABASE_URL_ENV:
    DATABASE_URL = _DATABASE_URL_ENV.replace(
        "postgresql://", "postgresql+psycopg2://"
    ).replace(
        "postgres://", "postgresql+psycopg2://"
    )
else:
    DATABASE_URL = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

# --- URL pour le checkpointer LangGraph (psycopg3, sans +psycopg2) ---
_CHECKPOINT_URI_ENV = os.getenv("CHECKPOINT_DB_URI")

if _CHECKPOINT_URI_ENV:
    CHECKPOINT_DB_URI = _CHECKPOINT_URI_ENV
else:
    CHECKPOINT_DB_URI = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")

# --- Serveur MCP ---
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001/mcp")