"""False-positive regression tests for legitimate banking, utility, promo, and normal SMS."""

from __future__ import annotations

from src.core.explanation import analyze_message


def test_legitimate_bank_debit_alert_with_defensive_otp_warning_is_safe() -> None:
    msg = (
        "A/c XX0000 debited for INR 1,450.00 on 11-11-26 at DemoMart via Ref No. 000000000000. "
        "If not done by you, call 1800-000-0000 or block card in official SampleBank app. Never share OTP."
    )
    res = analyze_message(msg)
    assert res.threat_category == "Safe / Normal"
    assert res.risk_level == "Low"
    assert res.rule_indicators == []
    assert not any(i.intent == "OTP collection" for i in res.detected_intents)


def test_legitimate_appointment_and_utility_notices_are_safe() -> None:
    appt = analyze_message(
        "Reminder: Your dental consultation at Sample Care Clinic is scheduled for tomorrow at 10:30 AM. Reply YES to confirm."
    )
    assert appt.threat_category == "Safe / Normal"
    assert appt.risk_level == "Low"

    utility = analyze_message(
        "SamplePower Electricity: Bill for Consumer No. 00000000 for Oct 2026 is Rs.1,120. Due date 25-11-2026. Pay via official portal or BBPS app."
    )
    assert utility.threat_category == "Safe / Normal"
    assert utility.risk_level == "Low"


def test_legitimate_promotional_offer_not_classified_as_scam() -> None:
    promo = analyze_message(
        "DemoMart Weekend Sale: Flat 20% off on fresh groceries above Rs.999. Use code DEMO20 in the DemoMart app before Sunday. T&C apply. Reply STOP to opt out."
    )
    assert promo.threat_category == "Promotional"
    assert promo.risk_level == "Low"


def test_casual_upi_and_family_texts_do_not_false_positive() -> None:
    casual_1 = analyze_message("Hey, can you send the dinner split of Rs 420 via UPI when you reach home?")
    assert casual_1.threat_category == "Safe / Normal"
    assert casual_1.risk_level == "Low"

    casual_2 = analyze_message("Your demo verification OTP is 000000. Do not share this OTP with anyone.")
    assert casual_2.threat_category == "Safe / Normal"
    assert casual_2.risk_level == "Low"
