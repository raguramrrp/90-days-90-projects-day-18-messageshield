"""Tests for text normalization, URL extraction, and UCI dataset loading."""

from __future__ import annotations

from pathlib import Path

from src.config import DATASET_PATH
from src.ml.data_loader import load_uci_sms_dataset
from src.ml.preprocessing import extract_urls, normalize_whitespace, preprocess_for_model


def test_normalize_whitespace_and_unicode() -> None:
    raw = "  URGENT\u00a0\u00a0KYC\tupdate\n\nnow!  "
    assert normalize_whitespace(raw) == "URGENT KYC update now!"


def test_extract_urls_ignores_currency_decimals() -> None:
    msg = (
        "A/c XX0000 debited for Rs.1,450.00 at 10.30 AM. "
        "Update KYC at https://samplebank-kyc.xyz/login?otp=1 or bit.ly/demo000 or http://203.0.113.5/pay"
    )
    urls = extract_urls(msg)
    assert urls == [
        "https://samplebank-kyc.xyz/login?otp=1",
        "bit.ly/demo000",
        "http://203.0.113.5/pay",
    ]


def test_extract_urls_skips_emails() -> None:
    msg = "Contact support@samplebank.example or visit www.samplebank.example/help"
    urls = extract_urls(msg)
    assert urls == ["www.samplebank.example/help"]


def test_preprocess_preserves_important_cues_and_replaces_urls() -> None:
    msg = "Do NOT share OTP! Pay Rs.50 at https://evil.xyz/pay now."
    processed = preprocess_for_model(msg)
    assert "not" in processed
    assert "otp" in processed
    assert "urltoken" in processed
    assert "currencytoken" in processed
    assert "!" in processed
    assert "evil.xyz" not in processed


def test_load_uci_dataset_validates_and_deduplicates(tmp_path: Path) -> None:
    sample_file = tmp_path / "SMSSpamCollection"
    sample_file.write_text(
        "ham\tHello how are you?\n"
        "ham\tHello how are you?\n"
        "spam\tWIN cash prize now!\n"
        "invalid_line_without_tab\n"
        "unknown\tsome message\n",
        encoding="utf-8",
    )
    df, stats = load_uci_sms_dataset(sample_file)
    assert stats.raw_rows == 3
    assert stats.missing_or_invalid_rows == 2
    assert stats.duplicate_rows_removed == 1
    assert stats.clean_rows == 2
    assert set(df["label"]) == {"ham", "spam"}


def test_real_uci_dataset_loads_cleanly() -> None:
    df, stats = load_uci_sms_dataset(DATASET_PATH)
    assert stats.raw_rows >= 5500
    assert stats.clean_rows > 5000
    assert stats.duplicate_rows_removed > 0
    assert stats.ham_count > stats.spam_count
    assert len(df) == stats.clean_rows
