"""Tests for screenshot OCR processing, failure handling, and batch CSV inspection/export."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import BASE_DIR, SAMPLE_CSV_PATH
from src.core.batch_analysis import (
    analyze_csv_bytes,
    export_batch_results_csv,
    inspect_csv_bytes,
)
from src.core.ocr_processor import extract_text_from_screenshot, get_ocr_status


def test_ocr_extracts_text_from_sample_screenshot_when_tesseract_present() -> None:
    ocr_ok, _ = get_ocr_status()
    assert ocr_ok is True

    scam_img = BASE_DIR / "data" / "sample_screenshots" / "sample_kyc_scam.png"
    res = extract_text_from_screenshot(scam_img.read_bytes(), scam_img.name)
    assert res.success is True
    assert "kyc" in res.extracted_text.lower()
    assert res.word_count >= 5


def test_ocr_fails_honestly_on_blank_and_invalid_files() -> None:
    blank_img = BASE_DIR / "data" / "sample_screenshots" / "blank_unreadable.png"
    blank_res = extract_text_from_screenshot(blank_img.read_bytes(), blank_img.name)
    assert blank_res.success is False
    assert blank_res.extracted_text == ""

    bad_ext = extract_text_from_screenshot(b"hello", "payload.exe")
    assert bad_ext.success is False
    assert "Unsupported image format" in bad_ext.message

    corrupt_png = extract_text_from_screenshot(b"not-a-real-png", "fake.png")
    assert corrupt_png.success is False
    assert corrupt_png.extracted_text == ""


def test_batch_csv_inspect_analyze_and_formula_safe_export() -> None:
    raw = SAMPLE_CSV_PATH.read_bytes()
    inspect_res = inspect_csv_bytes(raw, SAMPLE_CSV_PATH.name)
    assert inspect_res.suggested_column == "message"
    assert inspect_res.row_count == 15

    analyzed = analyze_csv_bytes(raw, SAMPLE_CSV_PATH.name, text_column="message")
    assert analyzed.processed_rows == 15
    assert analyzed.summary_counts["Suspicious / Flagged"] >= 10
    assert analyzed.summary_counts["Safe / Normal"] >= 3

    # Ensure formula injection characters are escaped cleanly on CSV export
    malicious_csv = b"text\n\"=CMD('calc')\"\n\"Hello friend\"\n"
    inj = analyze_csv_bytes(malicious_csv, "test.csv", text_column="text")
    exported = export_batch_results_csv(inj.results)
    assert "'=CMD" in exported


def test_batch_csv_rejects_invalid_extensions_and_missing_column() -> None:
    with pytest.raises(ValueError):
        inspect_csv_bytes(b"a,b\n1,2\n", "script.xlsx")
    with pytest.raises(ValueError):
        analyze_csv_bytes(b"text\nhi\n", "ok.csv", text_column="nonexistent")
