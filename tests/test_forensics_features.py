"""Tests for the 6 advanced TextVigil forensic capabilities."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.config import BASE_DIR
from src.core.explanation import analyze_message
from src.core.history import LocalStorage
from src.core.ocr_processor import extract_text_from_screenshot
from src.core.sender_analyzer import analyze_sender_id
from src.core.unicode_audit import audit_unicode_spoofing
from src.core.upi_dissector import dissect_all_upi_inputs
from src.main import app, get_storage


def test_qr_screenshot_and_upi_deep_link_dissection() -> None:
    qr_img = BASE_DIR / "data" / "sample_screenshots" / "sample_qr_upi_scam.png"
    ocr_res = extract_text_from_screenshot(qr_img.read_bytes(), qr_img.name)

    assert ocr_res.success is True
    assert ocr_res.detected_sender is not None
    assert "00000 00001" in ocr_res.detected_sender
    assert len(ocr_res.qr_payloads) == 1
    assert ocr_res.qr_payloads[0].startswith("upi://pay?")
    assert len(ocr_res.upi_previews) == 1

    preview = ocr_res.upi_previews[0]
    assert preview.payee_vpa == "demo-cashback@exampleupi"
    assert preview.amount == "4999"
    assert preview.is_outgoing_transfer is True
    assert preview.lure_contradiction is True
    assert preview.risk_level == "Critical"
    assert "OUTGOING payment" in preview.truth_statement

    full = analyze_message(
        raw_message=ocr_res.extracted_text,
        sender_id=ocr_res.detected_sender,
        qr_payloads=ocr_res.qr_payloads,
    )
    assert full.threat_category == "Financial Scam"
    assert full.risk_level == "Critical"
    assert len(full.upi_dissection) == 1
    assert full.sender_analysis.sender_type == "personal_mobile"

    mandate_img = BASE_DIR / "data" / "sample_screenshots" / "sample_qr_mandate_scam.png"
    mandate_ocr = extract_text_from_screenshot(mandate_img.read_bytes(), mandate_img.name)
    assert mandate_ocr.success is True
    assert mandate_ocr.detected_sender is not None and "00000 00002" in mandate_ocr.detected_sender
    assert len(mandate_ocr.upi_previews) == 1
    assert mandate_ocr.upi_previews[0].action_type == "mandate"
    assert mandate_ocr.upi_previews[0].payee_vpa == "demo-refund@testupi"


def test_direct_upi_link_in_text_is_dissected() -> None:
    items = dissect_all_upi_inputs(
        "Claim your Rs.2500 refund here: upi://pay?pa=demo-help@exampleupi&pn=Demo%20Support&am=2500&cu=INR"
    )
    assert len(items) == 1
    assert items[0].payee_vpa == "demo-help@exampleupi"
    assert items[0].is_personal_handle is True
    assert items[0].lure_contradiction is True


def test_trai_dlt_decoder_and_mobile_impersonation_and_official_channels() -> None:
    legit_dlt = analyze_sender_id("AD-DMOBNK-T", "A/c XX0000 debited at DemoMart.")
    assert legit_dlt.provided is True
    assert legit_dlt.sender_type == "trai_dlt_header"
    assert legit_dlt.operator_name == "Bharti Airtel"
    assert legit_dlt.circle_name == "Delhi NCR"
    assert legit_dlt.category_suffix == "T"
    assert legit_dlt.is_suspicious_mismatch is False

    promo_dlt = analyze_sender_id("JX-DMOKYC-P", "Your SampleBank KYC has expired today.")
    assert promo_dlt.operator_name == "Reliance Jio"
    assert promo_dlt.circle_name == "Karnataka"
    assert promo_dlt.is_suspicious_mismatch is True

    mobile_spoof = analyze_sender_id(
        "+91 00000 00002",
        "Your SampleBank account KYC needs immediate verification.",
    )
    assert mobile_spoof.sender_type == "personal_mobile"
    assert mobile_spoof.is_suspicious_mismatch is True

    res = analyze_message(
        "Your SampleBank account is temporarily restricted today.",
        sender_id="+91 00000 00002",
    )
    assert res.threat_category == "Impersonation"
    assert res.risk_level in {"High", "Critical"}
    assert any(
        ch.official_domain == "samplebank.example" and "1800-000-0000" in ch.helplines
        for ch in res.official_channels
    )


def test_unicode_homoglyph_zero_width_and_userinfo_audit() -> None:
    # Cyrillic 'ѕ' (U+0455) lookalike + invisible zero-width inside SampleBank / OTP
    sneaky = "Update your S\u200ba\u200bm\u200bp\u200bl\u200beBank K\u200bY\u200bC immediately with your O\u200bT\u200bP at https://\u0455amplebank-kyc.xyz/login"
    audit = audit_unicode_spoofing(sneaky)
    assert audit.has_obfuscation is True
    assert audit.zero_width_count >= 5
    assert audit.homoglyph_count >= 1
    assert "SAMPLEBANK" in audit.spoofed_brands

    res = analyze_message(sneaky)
    assert res.unicode_audit.has_obfuscation is True
    assert res.threat_category in {"Phishing", "OTP / Credential Theft"}
    assert res.risk_level in {"High", "Critical"}

    userinfo = analyze_message("Verify card at https://samplebank.example@demo-redirect.xyz/auth")
    assert userinfo.unicode_audit.has_obfuscation is True
    assert any(f.issue_type == "userinfo_trick" for f in userinfo.unicode_audit.findings)
    assert userinfo.url_analysis.has_suspicious_urls is True


def test_legitimate_indic_zero_width_joiners_not_falsely_flagged() -> None:
    # Genuine Malayalam chillu uses ZWNJ/ZWJ between Indic letters; must not false-positive
    malayalam = "നിങ്ങളുടെ അക്കൗണ്ട് ബാലൻസ്: അവ\u200dൻ വീട്ടിലാണ്"
    audit = audit_unicode_spoofing(malayalam)
    assert audit.has_obfuscation is False


def test_cross_message_campaign_matcher_and_recovery_triage_via_api(tmp_path: Path) -> None:
    db_path = tmp_path / "campaign_test.db"
    storage = LocalStorage(db_path=db_path)
    app.dependency_overrides[get_storage] = lambda: storage
    client = TestClient(app)

    try:
        r1 = client.post(
            "/api/analyze",
            json={
                "message": "Dear customer your SampleBank KYC has expired today. Account will be blocked in 2 hours. Update KYC at http://samplebank-one.xyz/verify or call 0000000001",
                "sender_id": "VK-DMOKYC",
                "source": "text",
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["campaign_match"]["has_match"] is False
        assert d1["recovery_triage"]["applicable"] is True
        assert any("1930" in step for step in d1["recovery_triage"]["immediate_steps"])

        # Rotated phishing domain with same script + callback number
        r2 = client.post(
            "/api/analyze",
            json={
                "message": "Dear customer your SampleBank KYC has expired today. Account will be blocked in 2 hours. Update KYC at http://samplebank-fresh.top/verify or call 0000000001",
                "sender_id": "JM-DMOKYC",
                "source": "text",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()
        cm = d2["campaign_match"]
        assert cm["has_match"] is True
        assert cm["match_count"] >= 1
        assert "+910000000001" in cm["shared_phones"]
        assert "samplebank-one.xyz" in cm["rotated_domains"]

        # Remote screen-share triage check
        r3 = client.post(
            "/api/analyze",
            json={
                "message": "Your debit card Rs.9,999 transaction is pending. Share OTP or install a remote screen-share app immediately.",
                "source": "text",
            },
        )
        assert r3.status_code == 200
        d3 = r3.json()
        assert "Airplane Mode" in " ".join(d3["recovery_triage"]["immediate_steps"])
    finally:
        app.dependency_overrides.clear()
