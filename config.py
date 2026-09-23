

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

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