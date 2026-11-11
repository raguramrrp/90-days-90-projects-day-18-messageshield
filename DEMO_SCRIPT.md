# TextVigil — 90-Second Portfolio Demo Script

Use this deterministic sequence when presenting **TextVigil** in interviews, hackathons, or portfolio walkthroughs.

## Setup Before Presenting

1. Run `.\run.bat` and open `http://127.0.0.1:8000` on a desktop browser (1440×900 or 1280×800).
2. Notice the centered Figma-style **iPhone 18 Pro** titanium frame (`390 × 844` viewport) with minimal **Phone Preview / Full Screen / Reset** controls in the top bar.

## Sequence (60–90 Seconds)

1. **0:00–0:15 · Home & Preview Experience**
   - Show the clean **Home** screen inside the iPhone 18 Pro bezel with custom **TextVigil** branding, primary **Scan Message** button, quick grouped actions (`Paste Message`, `Scan Screenshot`, `Sample Library`, `Batch CSV Scan`), and safety tip.
   - Toggle **Full Screen** and **Phone Preview** once to show responsive layout switching without duplicate DOM trees.

2. **0:15–0:35 · Plain-English Threat Report & Government Reporting**
   - Tap **Scan Message** -> **Fake KYC** sample -> **Analyse Message**.
   - On **Threat Report**, highlight:
     - Clean everyday summary (`Phishing · Critical Risk`), **Message Highlights** (`Links disabled`), and **Why It Was Checked As Critical Risk** (complex ML token scores stay hidden by default inside **Technical Signal Details**).
     - **Report to Government Portal**: tap **Copy & Report SMS on Sanchar Saathi** (or preview the complaint draft) showing how the classified message and structured complaint are copied to clipboard and opened directly on `sancharsaathi.gov.in` (or `cybercrime.gov.in`).

3. **0:35–0:55 · QR Cashback Forensics, TRAI Sender Check & Safe Family Warning**
   - Switch to **Screenshot** tab -> upload `data/sample_screenshots/sample_qr_upi_scam.png` -> highlight how OpenCV decodes `demo-cashback@exampleupi` (`₹4,999` outgoing transfer) and extracts dummy sender `+91 00000 00001` BEFORE payment apps open -> **Confirm & Analyse** -> show **Verify Safely Without Links**, **Copy Safe Family Warning** (`hxxp://` / `[.]`), and **Already tapped or paid?** Golden-Hour Recovery Triage.
   - Then run the **Bank Alert** sample (`AD-DMOBNK-T`) to demonstrate zero false positives on genuine alerts.

4. **0:55–1:15 · Batch CSV & Cross-Message Campaign Matching**
   - Switch to **Batch CSV** tab -> click **Run Bundled Demo CSV (15 Messages)** -> filter **Suspicious Only** and export `textvigil_batch_results.csv`.
   - Or load **Fake KYC** (`VK-DMOKYC`) followed by **Campaign #2** (`JM-DMOKYC-P` -> `samplebank-fresh.top`) in Paste SMS to surface the local **Recurring Scam Campaign Match** banner automatically.

5. **1:15–1:30 · Insights & Optional Technical Disclosure**
   - Tap **Insights** in the bottom navigation bar to show the plain-English overview first, then expand **Technical Model Details** to inspect Logistic Regression vs Multinomial Naive Bayes test-split metrics (`98.45%` accuracy, `99.12%` precision, `1` false positive out of 904 ham messages), Confusion Matrix, and **Threshold Explorer**.
