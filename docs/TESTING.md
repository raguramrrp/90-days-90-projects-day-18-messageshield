# Testing Documentation — TextVigil

## Test Suites

| Test File | Scope |
| --- | --- |
| `tests/test_preprocessing_and_data.py` | Unicode/whitespace normalization, decimal-safe URL extraction, email skip, scam-aware tokenization, UCI deduplication & loading |
| `tests/test_ml_pipeline.py` | Leakage-free stratified training, accuracy/precision/recall/F1/ROC-AUC checks, confusion matrix totals, threshold sensitivity |
| `tests/test_threat_and_url_engine.py` | Shorteners, raw IP URLs, brand lookalikes, official domain non-lookalike, KYC phishing, UPI collect, electricity cut-off, courier, job fee, OTP theft |
| `tests/test_false_positives.py` | Legitimate bank debit alerts with `"Never share OTP"`, dental appointment, official utility bill, retail promotional offer, casual UPI/OTP texts |
| `tests/test_forensics_features.py` | QR screenshot OpenCV decode + `upi://pay` deep-link dissection, TRAI DLT header & mobile impersonation checks, official verification helplines, Unicode zero-width/Cyrillic/userinfo spoof audit (+ Indic script false-positive guard), local cross-message campaign & rotated-domain matcher, and Golden-Hour recovery triage |
| `tests/test_ocr_and_batch.py` | Tesseract extraction on sample SMS image, blank/corrupt/unsupported file failure handling, CSV inspection/analysis, CSV formula-injection neutralization (`'=CMD`) |
| `tests/test_history_storage.py` | SQLite CRUD, search, category filtering, individual deletion, clear all, persistent settings |
| `tests/test_history_and_api.py` | FastAPI endpoint integration (`/api/health`, `/api/settings`, `/api/analyze`, `/api/history`, `/api/model/insights`, `/api/ocr/extract`, `/api/batch/*`) |

## Execution Commands (Windows PowerShell)

```powershell
# Run full automated suite + TypeScript typecheck
.\test.bat

# Or run pytest directly with coverage
.\.venv\Scripts\python.exe -m pytest -v tests/ --cov=src --cov-report=term-missing

# Frontend typecheck & production bundle check
npm --prefix frontend run build
```

## Observed Verification Results

- **Backend & ML Suite (`pytest`):** **30 / 30 passed** (`89%` total coverage across `src/`).
- **Frontend Build (`tsc --noEmit && vite build`):** **PASS** (0 TypeScript errors).
- **Live Browser E2E Verification (Headless Google Chrome via Playwright):** **PASS** across Desktop iPhone 18 Pro Frame (`1440×900` and `1280×768`), Full Screen toggle, Reset viewport, custom `TextVigil` brand assets loaded (`naturalWidth > 0`), absence of removed header/frame pill badges, complex ML matrices/token weights hidden by default behind expandable technical disclosures, Paste SMS + TRAI sender header decode, **Verify Safely Without Links** official directory, **One-Tap Defanged Family Warning** (`hxxp://` & `[.]`), **"Already Tapped or Paid?" Golden-Hour Recovery Triage**, Cross-Message Campaign rotated-domain match, Unicode homoglyph/zero-width spoof card, direct **Report to Government Portal** (`sancharsaathi.gov.in` & `cybercrime.gov.in`) clipboard copy & redirect check, Screenshot OCR negative (`blank_unreadable.png`) & QR UPI scam (`sample_qr_upi_scam.png`), Batch Demo CSV, History search & clear, Insights simple summary + expandable technical threshold slider, Sample Library -> Scanner handoff, Settings, and Mobile (`390×844`) responsive view with 0 console/page/5xx errors.

## Known Gaps

- Live external URL reputation lookups (e.g., VirusTotal) are intentionally disabled by default (`local_only`) and not exercised against external APIs during automated tests.
