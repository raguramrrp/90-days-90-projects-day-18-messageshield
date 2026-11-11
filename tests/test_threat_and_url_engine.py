"""Tests for threat categorization, suspicious phrases, URL inspection, and scam intents."""

from __future__ import annotations

from src.core.explanation import analyze_message
from src.core.url_inspector import inspect_urls


def test_url_inspector_detects_shorteners_ip_lookalike_and_query_params() -> None:
    msg = (
        "Click https://bit.ly/demo000 or http://203.0.113.44/kyc?otp=123 "
        "or https://samplebank-kyc-update.xyz/login?redirect=http://demo-phish.top"
    )
    summary = inspect_urls(msg)
    assert summary.count == 3
    assert summary.has_suspicious_urls is True
    assert summary.reputation_mode == "local_only"
    assert "structural only" in summary.reputation_notice.lower()

    bitly, ip_url, lookalike = summary.items
    assert bitly.is_shortened is True
    assert ip_url.is_ip_address is True
    assert ip_url.risk_level == "High"
    assert lookalike.is_lookalike_domain is True
    assert lookalike.lookalike_target == "SAMPLEBANK"
    assert lookalike.has_suspicious_tld is True
    assert lookalike.has_suspicious_params is True
    assert lookalike.risk_level == "High"


def test_official_domain_is_not_marked_lookalike() -> None:
    summary = inspect_urls("Check your statement at https://www.samplebank.example/personal")
    assert summary.count == 1
    assert summary.items[0].is_lookalike_domain is False
    assert summary.items[0].risk_level == "Low"


def test_indian_kyc_phishing_detection_and_explainability() -> None:
    msg = (
        "Dear customer, your SampleBank account KYC has expired today. "
        "Account will be blocked within 2 hours. Update KYC immediately at http://samplebank-kyc.xyz/verify"
    )
    result = analyze_message(msg)
    assert result.threat_category == "Phishing"
    assert result.risk_level in {"High", "Critical"}
    assert result.url_analysis.count == 1
    assert result.url_analysis.has_suspicious_urls is True
    assert any(r.rule_id == "fake_bank_kyc" for r in result.rule_indicators)
    assert any(i.intent == "Urgency or fear manipulation" for i in result.detected_intents)
    assert len(result.highlighted_spans) >= 2
    assert len(result.recommended_actions) >= 2


def test_upi_collect_and_electricity_and_courier_and_job_scams() -> None:
    upi = analyze_message(
        "Congratulations! Approve the UPI collect request and enter your UPI PIN to receive Rs.4999 cashback."
    )
    assert upi.threat_category == "Financial Scam"
    assert upi.risk_level == "Critical"
    assert any(i.intent == "Money transfer request" for i in upi.detected_intents)

    elec = analyze_message(
        "URGENT: Your electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Call electricity officer 0000000002."
    )
    assert elec.threat_category == "Impersonation"
    assert elec.risk_level == "Critical"

    courier = analyze_message(
        "Sample Parcel Service: Your parcel DEMO000001 is held due to incomplete address. Pay Rs.25 redelivery fee at http://parcel-redelivery-demo.xyz/pay"
    )
    assert courier.threat_category == "Financial Scam"
    assert any(i.intent == "Fake delivery fee" for i in courier.detected_intents)

    job = analyze_message(
        "Part-time Work From Home! Earn Rs.3500 daily reviewing sample videos online. Pay Rs.499 registration fee."
    )
    assert job.threat_category == "Financial Scam"
    assert any(i.intent == "Job registration fee" for i in job.detected_intents)

    otp = analyze_message(
        "Your bank card is on hold. Reply with your 6-digit OTP and install a remote screen-share app to cancel the Rs.9,999 charge."
    )
    assert otp.threat_category == "OTP / Credential Theft"
    assert otp.risk_level == "Critical"
    assert any(i.intent == "OTP collection" for i in otp.detected_intents)
