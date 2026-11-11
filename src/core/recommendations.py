"""Actionable, risk-specific safety recommendations and post-incident recovery triage."""

from __future__ import annotations

import re

from src.schemas import (
    IntentMatch,
    RecoveryTriagePlan,
    RuleIndicatorMatch,
    SenderAnalysis,
    UPIDissectionItem,
    URLSummary,
)

OFFICIAL_REPORTING_NOTE = (
    "TextVigil is an advisory safety assistant, not an official government portal. "
    "Use Report to Govt above or visit sancharsaathi.gov.in (Chakshu) for scam SMS/calls, "
    "and cybercrime.gov.in or helpline 1930 if financial fraud has occurred."
)

MOBILE_NUMBER_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?((?:[6-9]\d{9}|00000\d{5}))(?!\d)")
REMOTE_APP_RE = re.compile(r"(?i)\b(?:anydesk|teamviewer|quicksupport|rustdesk|screen[\s-]*share|\.apk\b|download\s+app)\b")


def build_recommendations(
    threat_category: str,
    risk_level: str,
    rule_hits: list[RuleIndicatorMatch],
    intents: list[IntentMatch],
    url_summary: URLSummary,
    upi_items: list[UPIDissectionItem] | None = None,
    sender_analysis: SenderAnalysis | None = None,
    has_unicode_obfuscation: bool = False,
) -> list[str]:
    """Return concise, practical next steps matched to the detected threat signals."""
    actions: list[str] = []
    rule_ids = {r.rule_id for r in rule_hits}
    intent_names = {i.intent for i in intents}

    if upi_items:
        actions.append(
            "Do NOT scan this QR code or enter your UPI PIN — scanning a pay QR or approving a collect request always sends money OUT."
        )

    if sender_analysis and sender_analysis.is_suspicious_mismatch:
        actions.append(
            "Do not trust the sender ID alone — verify inside the official bank/utility app or by dialing the helpline printed on your card/bill."
        )

    if has_unicode_obfuscation:
        actions.append(
            "Close this message immediately — disguised lookalike characters or hidden '@'/zero-width link tricks indicate intentional deception."
        )

    if url_summary.count > 0 and (
        url_summary.has_suspicious_urls
        or risk_level in {"Medium", "High", "Critical", "Needs Review"}
    ):
        actions.append(
            "Do not tap the embedded link or download any file or APK from the message."
        )

    if "otp_theft" in rule_ids or "OTP collection" in intent_names:
        actions.append(
            "Never share OTPs, ATM/UPI PINs, CVVs, or install screen-sharing apps like AnyDesk or QuickSupport."
        )

    if "upi_collect_manipulation" in rule_ids or "Money transfer request" in intent_names:
        actions.append(
            "Do not approve unfamiliar UPI collect requests or scan QR codes—receiving money never requires entering your UPI PIN."
        )

    if "fake_bank_kyc" in rule_ids or "banking_impersonation" in rule_ids:
        actions.append(
            "Open your bank's official mobile application independently or call the toll-free number printed on the back of your card."
        )

    if "electricity_disconnection" in rule_ids:
        actions.append(
            "Verify your electricity bill status directly through your official state utility portal or BBPS app—never call personal mobile numbers from threatening SMS alerts."
        )

    if "fake_courier_fee" in rule_ids or "Fake delivery fee" in intent_names:
        actions.append(
            "Track shipments only on the official courier website or app (e.g., India Post, BlueDart, DTDC) using your tracking ID—do not pay small redelivery fees through unknown links."
        )

    if "job_registration_fee" in rule_ids or "Job registration fee" in intent_names:
        actions.append(
            "Legitimate employers do not charge registration, training, or security deposits over WhatsApp or Telegram."
        )

    if "fake_loan_investment" in rule_ids or "Investment or loan promotion" in intent_names:
        actions.append(
            "Avoid upfront loan processing fees or guaranteed trading profit groups; verify lenders on the RBI registered NBFC list."
        )

    if "fake_reward_lottery" in rule_ids or "Reward manipulation" in intent_names:
        actions.append(
            "Treat unexpected prize, cashback, or lottery claims requiring fees or verification links as high-risk bait."
        )

    if threat_category == "Promotional" and not actions:
        actions = [
            "This appears to be a promotional or marketing message. Avoid clicking tracking links if you did not subscribe.",
            "Reply STOP or use the brand's official app preferences if you wish to opt out.",
        ]
    elif threat_category == "Safe / Normal" and not actions:
        actions = [
            "No common scam patterns or suspicious links were detected, though you should always confirm unexpected requests through official channels.",
        ]
    elif threat_category == "Needs Review" and not actions:
        actions = [
            "Evidence is mixed or inconclusive. Verify the sender directly using an official app or known contact number before acting.",
        ]

    deduped: list[str] = []
    for item in actions:
        if item not in deduped:
            deduped.append(item)
    return deduped[:5]


def build_recovery_triage(
    message: str,
    threat_category: str,
    sender_id: str | None,
    url_summary: URLSummary,
    upi_items: list[UPIDissectionItem],
    has_unicode_obfuscation: bool = False,
) -> RecoveryTriagePlan:
    """Build Golden-Hour post-incident triage steps tailored to what the message targeted."""
    applicable = (
        threat_category not in {"Safe / Normal", "Promotional"}
        or len(upi_items) > 0
        or has_unicode_obfuscation
    )
    if not applicable:
        return RecoveryTriagePlan(applicable=False)

    indicators: list[str] = []
    if sender_id and sender_id.strip():
        indicators.append(f"Sender: {sender_id.strip()}")
    for u in upi_items:
        if u.payee_vpa:
            indicators.append(f"Payee UPI ID: {u.payee_vpa}")
        if u.amount:
            indicators.append(f"UPI Amount: {u.currency} {u.amount}")
    for url_item in url_summary.items:
        defanged = (
            url_item.url.replace("https://", "hxxps://")
            .replace("http://", "hxxp://")
            .replace(".", "[.]")
        )
        indicators.append(f"Suspect Link: {defanged}")
    for m in MOBILE_NUMBER_RE.finditer(message or ""):
        num = f"+91-{m.group(1)}"
        entry = f"Phone Number: {num}"
        if entry not in indicators:
            indicators.append(entry)

    # Deduplicate indicators cleanly
    dedup_indicators = list(dict.fromkeys(indicators))[:6]

    lower = (message or "").lower()
    is_remote_rat = bool(REMOTE_APP_RE.search(message or ""))
    is_financial_or_otp = (
        len(upi_items) > 0
        or threat_category in {"Financial Scam", "OTP / Credential Theft", "Impersonation"}
        or any(kw in lower for kw in ("upi", "bank", "kyc", "otp", "card", "rs", "inr", "₹", "account"))
    )

    if is_remote_rat:
        return RecoveryTriagePlan(
            applicable=True,
            scenario_title="Remote Access / APK Exposure Protocol",
            urgency_banner="If you installed a screen-sharing app or APK from this message, disconnect internet access immediately before anything else.",
            immediate_steps=[
                "Turn on Airplane Mode (and turn off Wi-Fi) right now so any remote session loses live screen control.",
                "Uninstall AnyDesk, TeamViewer, QuickSupport, RustDesk, or any newly sideloaded APK from Settings > Apps.",
                "Using another trusted phone, call 1930 and your bank's fraud helpline to temporarily lock UPI, debit card, and NetBanking.",
                "Do not re-open banking apps until your device is clean and you have changed your NetBanking & UPI PIN.",
            ],
            evidence_to_keep=[
                "Original SMS/WhatsApp screenshot before blocking the sender",
                "12-digit UPI UTR / Bank transaction reference number (if debited)",
                "App package name / caller phone number shown in recent call logs",
            ],
            extracted_indicators=dedup_indicators,
        )

    if is_financial_or_otp:
        return RecoveryTriagePlan(
            applicable=True,
            scenario_title="Financial & UPI Fraud Golden Hour (First 60 Minutes)",
            urgency_banner="Acting within the first 1–2 hours gives cyber cells the best chance to freeze stolen funds in the recipient mule account.",
            immediate_steps=[
                "Call National Cyber Crime Helpline 1930 immediately AND submit details at cybercrime.gov.in using the pre-filled report.",
                "Contact your bank's official fraud helpline or use Mobile Banking to temporarily block your debit/credit card, UPI ID, and NetBanking.",
                "Save your 12-digit UPI UTR / Bank Ref number, exact debit time, and transaction amount from your banking app.",
                "Reset your NetBanking password and UPI PIN from the official bank app on a trusted device if any credential or OTP was entered.",
            ],
            evidence_to_keep=[
                "12-digit UPI UTR / Bank Transaction Reference ID",
                "Screenshot of SMS/WhatsApp thread and QR image (if scanned)",
                "Payee VPA, suspect URL, and sender phone number/header",
            ],
            extracted_indicators=dedup_indicators,
        )

    return RecoveryTriagePlan(
        applicable=True,
        scenario_title="Suspicious Link / Account Exposure Triage",
        urgency_banner="If you tapped the link or typed personal information, lock down your account before an attacker reuses your session.",
        immediate_steps=[
            "Close the opened webpage immediately — do not submit passwords, card numbers, or a second OTP.",
            "Change your account password from the official app or manually typed official website and enable 2-Step Verification.",
            "Check your email/SMS settings for unfamiliar forwarding rules or newly linked devices.",
            "Report the message on Sanchar Saathi (Chakshu) so telecom operators can block the sender header and domain.",
        ],
        evidence_to_keep=[
            "Screenshot of the original SMS and the opened browser URL bar",
            "Sender ID / phone number and timestamp",
        ],
        extracted_indicators=dedup_indicators,
    )
