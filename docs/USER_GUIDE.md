# User Guide — TextVigil

## 1. Desktop iPhone 18 Pro Preview vs Mobile Mode

- On desktop/laptop screens (`>= 768px`), TextVigil opens centered inside an **iPhone 18 Pro** titanium hardware frame (`390 × 844` scale) with realistic Dynamic Island and side keys.
- Use the top preview bar to toggle between **Phone Preview** and **Full Screen**, or click **Reset** to restore the default viewport.
- On smartphones or narrow mobile viewports (`< 768px`), the desktop bezel automatically disappears so the app uses the full screen natively.

## 2. Scanning a Message (`Scan` Tab)

### Paste SMS & TRAI Sender Check
1. Paste any suspicious SMS, WhatsApp text, or `upi://pay` deep-link (up to 2,000 characters), tap **Paste**, or load a quick demo sample.
2. Optionally enter the **Sender Header / Number** (e.g., `AD-DMOBNK-T` or `+91 00000 00001`) so TextVigil decodes the telecom operator/circle/type (`-S/-T/-P/-G`) and flags mobile numbers impersonating banks or utilities.
3. Tap **Analyse Message**.
4. Inspect the **Threat Report**: overall risk level, threat category, UPI/QR outgoing transfer truth card (if applicable), disguised Unicode/lookalike alerts, recurring scam campaign matches across local history, **Verify Safely Without Links** helplines, highlighted warning phrases, and plain-English reasons. Developers can tap **Technical Signal Details** for raw scores and token weights.

### Screenshot OCR & QR Payment Dissector
1. Switch to **Screenshot** inside the Scan screen.
2. Upload a `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, or `.tiff` screenshot (max 10 MB), including WhatsApp/SMS cashback or payment QR images.
3. TextVigil decodes embedded QR codes offline via OpenCV alongside local Tesseract OCR—exposing outgoing `upi://pay` VPA/amount traps and extracting visible sender headers automatically into editable confirmation inputs.
4. Review/correct extracted fields if needed, then tap **Confirm & Analyse Extracted Text**.

### Report, Warn Family Safely & Golden-Hour Recovery Triage
- **Report to Government Portal:** On flagged threats, tap **Copy & Report SMS on Sanchar Saathi** (`sancharsaathi.gov.in`) or **cybercrime.gov.in** to copy the exact message and formatted complaint to your clipboard and jump directly to the official portal.
- **Warn Family Safely:** Tap **Copy Safe Family Warning (Links Disabled)** to copy a clear 4-line summary where risky links and UPI handles are automatically neutralized (`hxxp://`, `[.]`, `[at]`) so relatives cannot accidentally tap the trap.
- **Already Tapped or Paid? Recovery Steps:** Expand this Golden-Hour triage panel for threat-tailored containment steps (Airplane Mode / uninstalling AnyDesk for remote-access threats, or 1930 + 12-digit UTR checklist + pre-extracted suspect domains/VPAs/phones for financial fraud).

### Batch CSV Scan
1. Switch to **Batch CSV** inside the Scan screen.
2. Upload a `.csv` file (up to 5 MB / 1,000 rows) or click **Run Bundled Demo CSV**.
3. Pick the message text column, run classification, filter **Suspicious Only**, and tap **Export CSV** for a formula-safe report.

## 3. History, Insights, Sample Library & Settings

- **History:** Search past local checks, filter by threat category, inspect saved reports, or delete individual/all records.
- **Insights:** View plain-English accuracy and protection coverage, or expand **Technical Model Details** for classifier comparison, Confusion Matrix, top n-grams, and the **Threshold Explorer**.
- **Sample Library:** Access 16 illustrative demonstration messages from **Home -> Sample Library** or **Scan -> Examples** (pre-filling both text and TRAI/mobile sender headers, including paired campaign-rotation, Cyrillic/punycode lookalike, UPI mandate, and `.apk` triage examples).
- **Settings:** Switch Warm Paper / Pure White theme, toggle local history saving, clear saved records, or expand **Advanced Detection Settings** to change the ML classifier or threshold.
