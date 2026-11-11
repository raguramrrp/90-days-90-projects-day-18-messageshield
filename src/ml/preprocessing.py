"""Scam-aware text normalization, URL extraction, and token preprocessing."""

from __future__ import annotations

import re
import unicodedata

# Matches http(s) URLs, www. URLs, or naked domains with common TLDs / paths
# while avoiding decimal amounts like Rs.1,450.00 or 10.30 AM.
URL_PATTERN = re.compile(
    r"(?i)\b(?:"
    r"(?:https?://|www\.)[^\s<>\"'\]\)]+"
    r"|"
    r"(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?/[^\s<>\"'\]\)]*"
    r"|"
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|in|co\.in|org\.in|gov\.in|net|org|ly|xyz|top|click|tk|ml|ga|cf|gq|"
    r"icu|vip|buzz|work|cam|loan|win|support|online|site|shop|club|info|live|rest|"
    r"cc|gy|gd|gl|at|to|me|io)"
    r"(?:/[^\s<>\"'\]\)]*)?"
    r")"
)

PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+?\d[\d\s\-]{7,13}\d)(?!\w)")
CURRENCY_AMOUNT_PATTERN = re.compile(r"(?i)(?:rs\.?|inr|₹|\$|£|€)\s*\d[\d,]*(?:\.\d{1,2})?")
LONG_DIGITS_PATTERN = re.compile(r"\b\d{5,}\b")
MULTISPACE_PATTERN = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Apply Unicode NFKC normalization and collapse redundant whitespace."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    # Strip ASCII control characters except standard spaces/newlines
    cleaned = "".join(
        ch if (ch == "\n" or ch == "\t" or ord(ch) >= 32) else " "
        for ch in normalized
    )
    return MULTISPACE_PATTERN.sub(" ", cleaned).strip()


def extract_urls(text: str) -> list[str]:
    """Extract unique URLs in order of appearance without opening or modifying targets."""
    if not text:
        return []
    seen: set[str] = set()
    urls: list[str] = []
    for match in URL_PATTERN.finditer(text):
        candidate = match.group(0).rstrip(".,;:!?)']\"")
        # Avoid false positives on email addresses when matched as bare domain
        start_idx = match.start()
        if start_idx > 0 and text[start_idx - 1] == "@":
            continue
        if candidate and candidate not in seen:
            seen.add(candidate)
            urls.append(candidate)
    return urls


def preprocess_for_model(text: str) -> str:
    """Normalize text for TF-IDF while preserving scam-relevant cues.

    Preserves important function words (e.g. 'not', 'never', 'your', 'now'),
    currency symbols, and exclamation/question marks while normalizing URLs,
    long phone numbers, and numeric reference IDs into structural tokens.
    """
    cleaned = normalize_whitespace(text)
    if not cleaned:
        return ""

    # Replace URLs before lowercasing so regex matches cleanly
    replaced = URL_PATTERN.sub(" urltoken ", cleaned)
    replaced = replaced.lower()
    # Preserve currency context explicitly
    replaced = CURRENCY_AMOUNT_PATTERN.sub(" currencytoken ", replaced)
    # Replace long phone numbers & account/reference numbers with structural cues
    replaced = PHONE_PATTERN.sub(" phonetoken ", replaced)
    replaced = LONG_DIGITS_PATTERN.sub(" numtoken ", replaced)
    # Separate exclamation / question marks so token_pattern captures them cleanly
    replaced = re.sub(r"([!?]+)", r" \1 ", replaced)
    return MULTISPACE_PATTERN.sub(" ", replaced).strip()
