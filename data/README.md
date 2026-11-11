# TextVigil Datasets & Bundled Demonstration Assets

## 1. UCI SMS Spam Collection v.1 (Primary ML Training & Evaluation Corpus)

- **Source:** UCI Machine Learning Repository — ID 228 (`https://archive.ics.uci.edu/dataset/228/sms+spam+collection`)
- **Citation / Authors:** Almeida, T.A., Gómez Hidalgo, J.M., Yamakami, A. (2011). *Contributions to the Study of SMS Spam Filtering: New Collection and Results.* Proceedings of the 2011 ACM Symposium on Document Engineering (DocEng '11).
- **License:** CC BY 4.0 / Public Academic Research Corpus.
- **Local File:** `data/raw/SMSSpamCollection` (auto-downloaded and verified by `scripts/download_dataset.py`).

### Schema & Preprocessing

- **Format:** Tab-separated values (`label<TAB>message`), UTF-8 text, no header row.
- **Raw rows:** 5,574
- **Exact duplicate removal:** 414 duplicate / conflicting messages removed **prior** to stratified 80/20 train/test splitting to prevent train-test data leakage.
- **Clean unique rows:** 5,160 (`4,518` legitimate `ham` / `87.56%`, `642` `spam` / `12.44%`).
- **Splits:** 4,128 training messages / 1,032 held-out test messages (`random_state=42`, stratified).

## 2. Bundled Demonstration Assets

Generated reproducibly via `python scripts/generate_demo_assets.py` for offline portfolio testing:

- `data/sample_batch_messages.csv` — 15 clearly synthetic illustrative messages mixing verified TRAI DLT safe alerts (`JD-CLINIC-S`, `AD-DMOBNK-T`, `JX-DISCOM-S`, `VK-DMOBSK-P`) with scam variants using dummy `+91 00000 0000x` numbers and `@exampleupi`/`@testupi` handles (fake KYC + rotated campaign domain, UPI `upi://pay` cashback link, UPI collect trap, fake courier fee, electricity cut-off mobile spoof, job fee, `.apk` E-Challan + remote screen-share, Cyrillic/Punycode/zero-width lookalikes, and fake prize RFC 5737 test IP link).
- `data/sample_screenshots/sample_kyc_scam.png` — Synthetic SMS screenshot (`VK-DMOKYC` · `SampleBank`) for verifying local Tesseract OCR extraction.
- `data/sample_screenshots/sample_legit_bank_alert.png` — Synthetic legitimate bank transaction alert screenshot (`AD-DMOBNK-T` · `SampleBank`).
- `data/sample_screenshots/sample_qr_upi_scam.png` — Synthetic WhatsApp/SMS QR cashback lure encoding `upi://pay?pa=demo-cashback@exampleupi...` under dummy `+91 00000 00001` for OpenCV QR payment forensics + OCR extraction.
- `data/sample_screenshots/sample_qr_mandate_scam.png` — Synthetic courier refund QR mandate lure encoding `upi://mandate?pa=demo-refund@testupi...` under dummy `+91 00000 00002` for AutoPay mandate dissection + mobile impersonation checks.
- `data/sample_screenshots/blank_unreadable.png` — Blank image used in negative OCR testing to verify graceful error handling.
