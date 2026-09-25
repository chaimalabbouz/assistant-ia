

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

RAW_PDF_PATH = RAW_DATA_DIR / "clark_county_hr_manual.pdf"
RAW_SECTIONS_PATH = PROCESSED_DATA_DIR / "raw_sections.json"
CHUNKS_PATH = PROCESSED_DATA_DIR / "chunks.jsonl"

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "hr_policy_chunks"

# --- Evaluation ---
EVAL_DIR = PROJECT_ROOT / "eval"
GOLDEN_DATASET_PATH = EVAL_DIR / "golden_dataset" / "hr_questions.json"
EVAL_RESULTS_DIR = EVAL_DIR / "results"


# --- PostgreSQL ---
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "hr_assistant_db"
POSTGRES_USER = "hr_admin"
POSTGRES_PASSWORD = "hr_password"

# --- Auth / Sécurité ---
# IMPORTANT : en production, cette clé doit venir d'une variable d'environnement,
# jamais être codée en dur. Pour le dev local, une valeur fixe suffit.
# Génère une vraie clé avec : python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = "CHANGE_ME_dev_only_secret_key_replace_before_prod"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 heures

# --- Database URL (construite depuis tes variables Postgres déjà définies) ---
DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)