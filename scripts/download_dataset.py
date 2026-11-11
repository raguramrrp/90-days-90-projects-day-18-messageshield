"""Download and verify the UCI SMS Spam Collection dataset.

Source:
    Almeida, T.A., Gomez Hidalgo, J.M., Yamakami, A. (2011).
    Contributions to the Study of SMS Spam Filtering: New Collection and Results.
    UCI Machine Learning Repository (ID 228).
"""

from __future__ import annotations

import hashlib
import io
import ssl
import sys
import urllib.request
import zipfile
from pathlib import Path

UCI_PRIMARY_URL = (
    "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
)
UCI_LEGACY_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip"
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
TARGET_FILE = RAW_DIR / "SMSSpamCollection"
README_FILE = RAW_DIR / "readme"


def _build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _download_bytes(url: str, timeout: int = 30) -> bytes:
    ctx = _build_ssl_context()
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TextVigil-Dataset-Fetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read()


def ensure_uci_dataset(force: bool = False) -> Path:
    """Ensure data/raw/SMSSpamCollection exists locally; download from UCI if missing."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if TARGET_FILE.exists() and TARGET_FILE.stat().st_size > 100_000 and not force:
        return TARGET_FILE

    urls = [UCI_PRIMARY_URL, UCI_LEGACY_URL]
    last_error: Exception | None = None
    for url in urls:
        try:
            print(f"[*] Downloading UCI SMS Spam Collection from {url} ...")
            archive_bytes = _download_bytes(url)
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
                names = zf.namelist()
                sms_member = next(
                    (n for n in names if n.lower().endswith("smsspamcollection")),
                    None,
                )
                if sms_member is None:
                    raise ValueError(f"SMSSpamCollection not found inside archive: {names}")

                TARGET_FILE.write_bytes(zf.read(sms_member))
                readme_member = next(
                    (n for n in names if Path(n).name.lower() == "readme"),
                    None,
                )
                if readme_member:
                    README_FILE.write_bytes(zf.read(readme_member))

            digest = hashlib.sha256(TARGET_FILE.read_bytes()).hexdigest()[:16]
            line_count = len(
                TARGET_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
            )
            print(
                f"[OK] Saved {TARGET_FILE} ({line_count} rows, sha256:{digest}...)"
            )
            return TARGET_FILE
        except Exception as exc:
            last_error = exc
            print(f"[WARN] Download failed from {url}: {exc}")

    raise RuntimeError(f"Could not download UCI SMS Spam Collection: {last_error}")


if __name__ == "__main__":
    force_flag = "--force" in sys.argv
    path = ensure_uci_dataset(force=force_flag)
    print(f"Dataset ready: {path}")
