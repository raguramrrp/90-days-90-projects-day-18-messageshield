"""Scam intent detection with explicit matched phrase evidence."""

from __future__ import annotations

import re
from pathlib import Path

from src.config import RULES_PATH
from src.core.threat_rules import load_threat_rules
from src.schemas import IntentMatch

INTENT_EXPLANATIONS = {
    "Money transfer request": "Asks the recipient to pay, transfer, deposit, or approve a payment request.",
    "Credential collection": "Requests sensitive login, KYC, card, or identity details via link or form.",
    "OTP collection": "Prompts the recipient to share, reply with, or enter a one-time passcode.",
    "Reward manipulation": "Uses unexpected prizes, cashbacks, or lottery winnings as bait.",
    "Urgency or fear manipulation": "Pressures immediate action using account block, disconnection, or deadline threats.",
    "Account verification": "Claims an account, wallet, or KYC status needs urgent verification or reactivation.",
    "Fake delivery fee": "Claims a parcel or courier delivery requires a payment or address update.",
    "Job registration fee": "Promises high daily pay or job placement tied to fees or informal messaging.",
    "Investment or loan promotion": "Pushes instant no-CIBIL loans or guaranteed financial/trading returns.",
    "Impersonation": "Presents unverified contact channels or links alongside institutional or utility references.",
}


def detect_scam_intents(
    text: str,
    rules_path: Path = RULES_PATH,
) -> list[IntentMatch]:
    """Identify likely manipulative or transactional message intents with evidence."""
    config = load_threat_rules(str(rules_path))
    detected: list[IntentMatch] = []

    for rule in config.get("intent_rules", []):
        excluded = rule.get("excluded_if_matches", [])
        if any(re.search(pat, text, flags=re.IGNORECASE | re.DOTALL) for pat in excluded):
            continue

        matched_phrases: list[str] = []
        for pattern in rule.get("patterns", []):
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                snippet = match.group(0).strip()
                if snippet and snippet not in matched_phrases:
                    matched_phrases.append(snippet)

        if matched_phrases:
            intent_name = rule["intent"]
            detected.append(
                IntentMatch(
                    intent=intent_name,
                    reason=INTENT_EXPLANATIONS.get(
                        intent_name, f"Matched indicators for {intent_name.lower()}."
                    ),
                    matched_phrases=matched_phrases,
                )
            )

    return detected
