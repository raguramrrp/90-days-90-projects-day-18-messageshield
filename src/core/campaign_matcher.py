"""Local cross-message campaign and domain-rotation playbook matcher."""

from __future__ import annotations

import re

from src.ml.preprocessing import extract_urls
from src.schemas import (
    CampaignMatchSummary,
    HistoryRecord,
    UPIDissectionItem,
    URLSummary,
)

MOBILE_EXTRACT_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?((?:[6-9]\d{9}|00000\d{5}))(?!\d)")
VPA_EXTRACT_RE = re.compile(r"\b([a-zA-Z0-9._-]{2,64}@(?:ybl|oksbi|okicici|okaxis|okhdfcbank|paytm|ibl|axl|upi|apl|yapl|rapl|fbl|idfcbank|jio|ikwik|exampleupi|testupi|invalidupi))\b", re.IGNORECASE)
URL_MASK_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+|(?:[a-z0-9-]+\.)+(?:com|in|xyz|top|click|tk|ml|ga|cf|gq|icu|vip|online|site|shop|ly|co\.in)\S*")
CURRENCY_MASK_RE = re.compile(r"(?i)(?:rs\.?|inr|₹|\$)\s*[\d,]+(?:\.\d{1,2})?")
DATE_OR_NUM_MASK_RE = re.compile(r"\b\d{1,4}[-/:]\d{1,4}(?:[-/:]\d{1,4})?\b|\b\d{3,}\b")


def _extract_mobile_set(text: str, sender_id: str | None = None) -> set[str]:
    phones: set[str] = set()
    for src in (text, sender_id or ""):
        for m in MOBILE_EXTRACT_RE.finditer(src):
            digits = m.group(1)
            phones.add(f"+91{digits}")
    return phones


def _extract_vpa_set(text: str, upi_items: list[UPIDissectionItem] | None = None) -> set[str]:
    vpas = {m.group(1).lower() for m in VPA_EXTRACT_RE.finditer(text or "")}
    for u in upi_items or []:
        if u.payee_vpa:
            vpas.add(u.payee_vpa.strip().lower())
    return vpas


def _extract_host_set(url_summary: URLSummary) -> set[str]:
    return {
        u.host.lower().removeprefix("www.")
        for u in url_summary.items
        if u.host and u.host.strip()
    }


def _skeleton_tokens(text: str) -> set[str]:
    cleaned = URL_MASK_RE.sub(" __url__ ", text or "")
    cleaned = VPA_EXTRACT_RE.sub(" __vpa__ ", cleaned)
    cleaned = MOBILE_EXTRACT_RE.sub(" __phone__ ", cleaned)
    cleaned = CURRENCY_MASK_RE.sub(" __amt__ ", cleaned)
    cleaned = DATE_OR_NUM_MASK_RE.sub(" __num__ ", cleaned)
    words = re.findall(r"[a-z]{3,}|__[a-z]+__", cleaned.lower())
    stopwords = {
        "the",
        "and",
        "for",
        "your",
        "you",
        "are",
        "with",
        "this",
        "that",
        "from",
        "has",
        "have",
        "will",
        "now",
    }
    return {w for w in words if w not in stopwords}


def find_campaign_matches(
    message: str,
    sender_id: str | None,
    url_summary: URLSummary,
    upi_items: list[UPIDissectionItem],
    prior_flagged_records: list[HistoryRecord] | None,
    threat_category: str,
) -> CampaignMatchSummary:
    """Compare current suspicious message against local SQLite flagged history."""
    if not prior_flagged_records or threat_category in {"Safe / Normal", "Promotional"}:
        return CampaignMatchSummary()

    cur_tokens = _skeleton_tokens(message)
    cur_phones = _extract_mobile_set(message, sender_id=sender_id)
    cur_vpas = _extract_vpa_set(message, upi_items=upi_items)
    cur_domains = _extract_host_set(url_summary)

    matched_ids: list[int] = []
    shared_phones: set[str] = set()
    shared_vpas: set[str] = set()
    shared_domains: set[str] = set()
    rotated_domains: set[str] = set()
    max_sim = 0.0

    for rec in prior_flagged_records:
        if rec.threat_category in {"Safe / Normal", "Promotional"}:
            continue

        rec_phones = _extract_mobile_set(rec.message, sender_id=(rec.full_result or {}).get("sender_id"))
        rec_vpas = _extract_vpa_set(rec.message)
        for upi_obj in (rec.full_result or {}).get("upi_dissection", []) or []:
            vpa = str(upi_obj.get("payee_vpa") or "").strip().lower()
            if vpa:
                rec_vpas.add(vpa)
        rec_domains: set[str] = set()
        for item in rec.url_indicators or []:
            host = str(item.get("host", "")).lower().removeprefix("www.")
            if host:
                rec_domains.add(host)
        if not rec_domains:
            for u in extract_urls(rec.message):
                host_guess = u.split("://", 1)[-1].split("/", 1)[0].split("?", 1)[0].lower().removeprefix("www.")
                if host_guess:
                    rec_domains.add(host_guess)

        rec_tokens = _skeleton_tokens(rec.message)
        union = cur_tokens | rec_tokens
        sim = len(cur_tokens & rec_tokens) / len(union) if union else 0.0

        p_overlap = cur_phones & rec_phones
        v_overlap = cur_vpas & rec_vpas
        d_overlap = cur_domains & rec_domains

        is_template_match = sim >= 0.48 and len(cur_tokens & rec_tokens) >= 4
        if is_template_match or p_overlap or v_overlap or d_overlap:
            matched_ids.append(rec.id)
            shared_phones.update(p_overlap)
            shared_vpas.update(v_overlap)
            shared_domains.update(d_overlap)
            max_sim = max(max_sim, sim)

            if is_template_match and cur_domains and rec_domains and not d_overlap:
                # Same scam script skeleton using a fresh/rotated domain
                for rd in rec_domains:
                    rotated_domains.add(rd)

    if not matched_ids:
        return CampaignMatchSummary()

    parts: list[str] = []
    if rotated_domains:
        parts.append(
            f"reuses an earlier scam script with a rotated link domain (previously saw {', '.join(sorted(rotated_domains)[:2])})"
        )
    if shared_phones:
        parts.append(f"shares callback number {', '.join(sorted(shared_phones)[:2])}")
    if shared_vpas:
        parts.append(f"shares UPI ID {', '.join(sorted(shared_vpas)[:2])}")
    if shared_domains:
        parts.append(f"repeats domain {', '.join(sorted(shared_domains)[:2])}")
    if not parts:
        parts.append(f"closely matches wording structure ({int(round(max_sim * 100))}% similarity)")

    count = len(matched_ids)
    summary = (
        f"Similar to {count} previously flagged scan{'s' if count != 1 else ''} on your device: "
        + "; ".join(parts)
        + "."
    )

    return CampaignMatchSummary(
        has_match=True,
        match_count=count,
        matched_record_ids=matched_ids[:10],
        shared_phones=sorted(shared_phones)[:5],
        shared_vpas=sorted(shared_vpas)[:5],
        shared_domains=sorted(shared_domains)[:5],
        rotated_domains=sorted(rotated_domains)[:5],
        similarity_score=round(max_sim, 2),
        summary=summary,
    )
