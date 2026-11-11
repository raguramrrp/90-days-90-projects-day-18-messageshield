# Project Overview — TextVigil

## Problem Statement

Everyday smartphone users frequently receive SMS, WhatsApp, and RCS messages impersonating banks, UPI apps, electricity boards, courier companies, and job recruiters. Traditional academic spam classifiers only output a binary `spam` / `ham` label, which leaves users asking:
- *Why* was this message flagged?
- Does it contain a fake link or lookalike domain?
- Is a legitimate bank transaction alert (`"A/c debited... Never share OTP"`) actually safe?
- What concrete steps should I take next?

## Objectives

1. Deliver a realistic, touch-first **mobile cybersecurity app UI** (with a desktop smartphone preview frame and responsive full-screen mobile browser mode).
2. Combine a **leakage-free NLP baseline** (TF-IDF + Logistic Regression & Multinomial Naive Bayes trained on the UCI SMS Spam Collection) with **transparent, modular Indian scam indicators**, **scam intent detection**, and **offline URL structural inspection**.
3. Provide **honest explainability**: keep uncalibrated ML probabilities distinct from the overall threat verdict, attribute every signal to its source (ML vs rule vs URL vs defensive guard), and avoid false positives on legitimate alerts.
4. Keep user data **private and local by default** (SQLite storage, local Tesseract OCR, zero automatic link opening, zero required paid APIs).

## Scope & MVP Boundaries

- **Included:** Single-SMS inspection, screenshot OCR extraction with mandatory user review, 8-category threat taxonomy + `Needs Review`, 10 scam intent detectors, India scam rule module (`config/threat_rules.json`), structural URL analysis, local SQLite history with search/filter/delete, batch CSV classification with formula-safe export, real model evaluation insights with threshold explorer, and settings persistence.
- **Explicitly Excluded:** Live cellular SMS interception (browser sandbox constraint), user accounts/cloud sync, paid third-party threat-intel calls by default, and live crawling/opening of suspicious URLs.
