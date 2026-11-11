# Development Notes — Design Decisions & Trade-offs

## 1. Hybrid ML + Modular Rules Architecture
- The UCI SMS Spam Collection (2011) is a binary (`ham` vs `spam`) English/UK & global SMS corpus. It does not independently contain labeled classes for modern Indian scams such as UPI collect-request traps, Aadhaar/PAN KYC threats, or BESCOM/electricity disconnection impersonation.
- Therefore, TextVigil uses the trained TF-IDF + Logistic Regression / Multinomial Naive Bayes pipeline strictly as a **statistical spam baseline**, layered with modular transparent rules (`config/threat_rules.json`), 10 scam intent detectors, and offline URL structural checks.
- Every prediction explicitly reports `category_source` (`Combined ML Model + India Threat Rules`, `Transparent Rule & URL Indicators`, `Trained NLP Classifier Baseline`, `Benign Context Guard`, or `Needs Review`) so users never confuse rule matches with ML training labels.

## 2. Preventing Data Leakage & Preserving Scam Signals
- Exact duplicate and cross-label colliding rows (`414` out of `5,574`) are removed **before** the stratified 80/20 split (`random_state=42`).
- `TfidfVectorizer` is wrapped inside a scikit-learn `Pipeline` and fitted strictly on `X_train`.
- Standard English stopword lists are intentionally avoided because words like `not`, `never`, `your`, `now`, `call`, and `free`, along with currency markers (`₹`, `$`, `£`) and `!`/`?`, carry strong spam/safety semantics.

## 3. False-Positive Restraint
- Legitimate Indian bank transaction alerts routinely contain words like `"OTP"`, `"UPI"`, `"A/c"`, `"debited"`, and `"block card"`.
- Both `otp_theft` rules and `OTP collection` intent rules enforce negative context exclusions (`excluded_if_matches`) when messages contain defensive phrasing like `"Never share OTP"` or `"Do not share OTP with anyone"`, alongside `benign_context_patterns` for standard debit/credit notifications, appointment confirmations, and official utility notices.

## 4. Tesseract OCR vs EasyOCR on Windows
- Tesseract v5 (`pytesseract`) paired with OpenCV grayscale conversion, dynamic upscaling, dark-mode inversion, and Otsu thresholding runs locally in milliseconds without downloading multi-hundred-megabyte PyTorch weights.
- `src/config.py` auto-detects `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows even when Tesseract is omitted from the user `PATH`.

## 5. Single-Viewport React Shell
- `PhoneFrameShell.tsx` wraps a **single** React application tree using responsive Tailwind `md:` classes instead of duplicating separate desktop/mobile component trees, ensuring shared scroll refs, unique element IDs, and preserved form state across viewport switches.
