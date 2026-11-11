# Troubleshooting Guide (Windows)

## 1. `Python 3.10+ was not found` or Wheel Build Errors on Python 3.14
- **Cause:** Some compiled ML/CV wheels (`scikit-learn`, `scipy`, `opencv-python-headless`) lag behind the newest Python major release or require C++ Build Tools if built from source.
- **Fix:** Install **Python 3.12 (64-bit)** from `python.org`. `setup.bat` automatically prefers `py -3.12` when present.

## 2. `SSL: CERTIFICATE_VERIFY_FAILED` When Downloading UCI Dataset
- **Cause:** Windows system date mismatch or an outdated Python stdlib CA bundle.
- **Fix:** Ensure `certifi` is installed inside `.venv` (`pip install certifi`) and verify system clock/date. `scripts/download_dataset.py` uses `certifi.where()` automatically.

## 3. Screenshot OCR Reports `"Tesseract OCR not found"`
- **Cause:** Tesseract OCR binary is not installed or is in a non-standard directory.
- **Fix:**
  1. Install Tesseract OCR for Windows (UB Mannheim installer) to `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  2. Or set `TESSERACT_CMD=C:\Your\Custom\Path\tesseract.exe` in `.env`.
  3. Paste SMS and Batch CSV scanning continue to work even without Tesseract.

## 4. `EPERM` or Missing `frontend/dist` When Starting `run.bat`
- **Fix:** Run `npm --prefix frontend install` and `npm --prefix frontend run build` manually in PowerShell, then re-run `.\run.bat`.

## 5. Port `8000` Already in Use
- **Fix:** Stop any other local server on port 8000 or change `MS_PORT` in `.env` and start with:
  ```powershell
  .\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8010
  ```
