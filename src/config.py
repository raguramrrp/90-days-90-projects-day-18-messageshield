"""Application configuration, paths, upload limits, and Tesseract discovery."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _resolve_path(env_key: str, default_rel: str) -> Path:
    raw = os.getenv(env_key, default_rel)
    p = Path(raw)
    return p if p.is_absolute() else BASE_DIR / p


APP_NAME = os.getenv("MS_APP_NAME", "TextVigil")
HOST = os.getenv("MS_HOST", "127.0.0.1")
PORT = int(os.getenv("MS_PORT", "8000"))

DATASET_PATH = _resolve_path("MS_DATASET_PATH", "data/raw/SMSSpamCollection")
DB_PATH = _resolve_path("MS_DB_PATH", "data/messageshield.db")
MODEL_PATH = _resolve_path("MS_MODEL_PATH", "models/messageshield_models.joblib")
EVAL_PATH = _resolve_path("MS_EVAL_PATH", "models/evaluation_report.json")
RULES_PATH = _resolve_path("MS_RULES_PATH", "config/threat_rules.json")
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
SAMPLE_CSV_PATH = BASE_DIR / "data" / "sample_batch_messages.csv"

MAX_IMAGE_MB = int(os.getenv("MS_MAX_IMAGE_MB", "10"))
MAX_CSV_MB = int(os.getenv("MS_MAX_CSV_MB", "5"))
MAX_CSV_ROWS = int(os.getenv("MS_MAX_CSV_ROWS", "1000"))
MAX_MESSAGE_CHARS = int(os.getenv("MS_MAX_MESSAGE_CHARS", "2000"))
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

DEFAULT_URL_REPUTATION_PROVIDER = os.getenv("MS_URL_REPUTATION_PROVIDER", "local_only")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "").strip()

COMMON_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    "/usr/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/opt/homebrew/bin/tesseract",
]


def resolve_tesseract_path() -> str | None:
    """Locate Tesseract OCR binary from env override, PATH, or standard locations."""
    env_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if env_cmd and Path(env_cmd).is_file():
        return env_cmd

    which_cmd = shutil.which("tesseract")
    if which_cmd and Path(which_cmd).is_file():
        return which_cmd

    for candidate in COMMON_TESSERACT_PATHS:
        if Path(candidate).is_file():
            return candidate
    return None
