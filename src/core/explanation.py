"""Unified explainable threat combiner, forensics orchestrator, and risk scorer."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from src.config import MODEL_PATH, RULES_PATH
from src.core.campaign_matcher import find_campaign_matches
from src.core.intent_detection import detect_scam_intents
from src.core.recommendations import (
    OFFICIAL_REPORTING_NOTE,
    build_recommendations,
    build_recovery_triage,
)
from src.core.sender_analyzer import analyze_sender_id, detect_official_verification_channels
from src.core.threat_rules import evaluate_threat_rules, load_threat_rules
from src.core.unicode_audit import audit_unicode_spoofing, deobfuscate_for_matching
from src.core.upi_dissector import dissect_all_upi_inputs
from src.core.url_inspector import inspect_urls
from src.ml.prediction import predict_message
from src.ml.preprocessing import normalize_whitespace
from src.schemas import (
    AnalyzeResponse,
    HighlightedSpan,
    HistoryRecord,
    RuleIndicatorMatch,
)

CATEGORY_SOURCE_LABELS = {
    "ml_and_rules": "Combined ML Model + India Threat Rules",
    "rule_indicator": "Transparent Rule, URL & Forensic Indicators",
    "ml_baseline": "Trained NLP Classifier Baseline (UCI SMS Corpus)",
    "defensive_context": "Benign Context Guard + ML Verification",
    "insufficient_evidence": "Borderline Signals (Needs Human Review)",
}

SEVERITY_RANK = {"info": 0, "medium": 1, "high": 2, "critical": 3}
RISK_ORDER = {"Low": 0, "Needs Review": 1, "Medium": 2, "High": 3, "Critical": 4}


def _deduplicate_overlapping_spans(spans: list[HighlightedSpan]) -> list[HighlightedSpan]:
    """Sort spans by start position and severity, resolving overlaps cleanly."""
    ordered = sorted(
        spans,
        key=lambda s: (s.start, -SEVERITY_RANK.get(s.severity, 0), -(s.end - s.start)),
    )
    resolved: list[HighlightedSpan] = []
    last_end = -1
    for span in ordered:
        if span.start >= last_end and span.end > span.start:
            resolved.append(span)
            last_end = span.end
    return resolved


def analyze_message(
    raw_message: str,
    model_name: str | None = None,
    threshold: float = 0.50,
    url_reputation_mode: str = "local_only",
    model_path: Path = MODEL_PATH,
    rules_path: Path = RULES_PATH,
    sender_id: str | None = None,
    qr_payloads: list[str] | None = None,
    prior_flagged_records: list[HistoryRecord] | None = None,
) -> AnalyzeResponse:
    """Run hybrid ML, rules, URL, Unicode, UPI/QR, TRAI DLT sender, and campaign analysis."""
    # Inspect raw characters BEFORE whitespace/NFKC cleanup so invisible evasion tricks are caught
    unicode_audit = audit_unicode_spoofing(raw_message)

    message = normalize_whitespace(raw_message)
    if not message:
        raise ValueError("Message text cannot be empty.")

    deobfuscated = deobfuscate_for_matching(raw_message)
    eval_text = normalize_whitespace(deobfuscated) if unicode_audit.has_obfuscation else message

    qr_http_urls = [
        p.strip()
        for p in (qr_payloads or [])
        if p and p.strip().lower().startswith(("http://", "https://", "www."))
    ]
    url_scan_text = eval_text if not qr_http_urls else f"{eval_text} {' '.join(qr_http_urls)}"

    ml_pred = predict_message(
        text=eval_text,
        model_name=model_name,
        threshold=threshold,
        model_path=model_path,
    )
    rules_eval = evaluate_threat_rules(eval_text, rules_path=rules_path)
    url_summary = inspect_urls(
        url_scan_text,
        reputation_mode=url_reputation_mode,
        rules_path=rules_path,
    )
    intents = detect_scam_intents(eval_text, rules_path=rules_path)
    upi_dissection = dissect_all_upi_inputs(eval_text, qr_payloads=qr_payloads)
    sender_analysis = analyze_sender_id(sender_id=sender_id, message=eval_text)

    rule_models = [
        RuleIndicatorMatch(
            rule_id=hit.rule_id,
            label=hit.label,
            category=hit.category,
            severity=hit.severity,  # type: ignore[arg-type]
            description=hit.description,
            matched_text=hit.matched_text,
        )
        for hit in rules_eval.scam_hits
    ]
    benign_labels = [b["label"] for b in rules_eval.benign_context_hits]

    ml_is_spam = ml_pred.ml_classification == "Spam / Suspicious"
    high_risk_urls = [u for u in url_summary.items if u.risk_level == "High"]
    medium_risk_urls = [u for u in url_summary.items if u.risk_level == "Medium"]

    # Baseline hybrid decision logic
    risk_score = 0.0
    if rules_eval.scam_hits:
        top_rule = max(rules_eval.scam_hits, key=lambda h: (SEVERITY_RANK.get(h.severity, 1), h.weight))
        threat_category = top_rule.category
        category_source = "ml_and_rules" if ml_is_spam else "rule_indicator"
        rule_sum = sum(h.weight for h in rules_eval.scam_hits)
        url_boost = max((u.risk_score for u in url_summary.items), default=0.0) * 0.40
        ml_boost = ml_pred.raw_spam_score * 0.25
        risk_score = min(1.0, 0.35 + rule_sum + url_boost + ml_boost)
        if top_rule.severity == "critical" or risk_score >= 0.80 or (high_risk_urls and len(rules_eval.scam_hits) >= 1):
            risk_level = "Critical"
        else:
            risk_level = "High"
        classification = "Suspicious / Scam Threat"

    elif high_risk_urls or (url_summary.has_suspicious_urls and (ml_is_spam or len(intents) > 0)):
        threat_category = "Phishing"
        category_source = "ml_and_rules" if ml_is_spam else "rule_indicator"
        max_url = max((u.risk_score for u in url_summary.items), default=0.45)
        risk_score = min(1.0, 0.45 + max_url * 0.5 + (0.15 if ml_is_spam else 0.0))
        risk_level = "High" if (high_risk_urls or ml_is_spam) else "Medium"
        classification = "Suspicious Link / Phishing Risk"

    elif rules_eval.promotional_hits and not rules_eval.scam_hits and not high_risk_urls:
        threat_category = "Promotional"
        category_source = "ml_and_rules" if ml_is_spam else "rule_indicator"
        risk_score = round(0.18 + (0.20 if medium_risk_urls else 0.0) + (0.12 if ml_is_spam else 0.0), 2)
        risk_level = "Medium" if medium_risk_urls else "Low"
        classification = "Promotional / Marketing"

    elif rules_eval.benign_context_hits and not rules_eval.scam_hits and not url_summary.has_suspicious_urls:
        threat_category = "Safe / Normal"
        category_source = "defensive_context"
        risk_score = round(min(0.24, ml_pred.raw_spam_score * 0.35), 2)
        risk_level = "Low"
        classification = "Legitimate / Informational"

    elif ml_is_spam:
        intent_names = {i.intent for i in intents}
        if "Reward manipulation" in intent_names:
            threat_category = "Fake Reward"
        elif "Money transfer request" in intent_names or "Investment or loan promotion" in intent_names:
            threat_category = "Financial Scam"
        elif "Credential collection" in intent_names or "Account verification" in intent_names:
            threat_category = "Phishing"
        elif ml_pred.raw_spam_score >= max(threshold + 0.14, 0.65) or len(intents) > 0:
            threat_category = "General Spam"
        else:
            threat_category = "Needs Review"

        if threat_category == "Needs Review":
            category_source = "insufficient_evidence"
            risk_level = "Needs Review"
            risk_score = round(min(0.49, ml_pred.raw_spam_score * 0.75), 2)
            classification = "Needs Review"
        else:
            category_source = "ml_and_rules" if intents else "ml_baseline"
            risk_score = round(min(0.85, 0.45 + ml_pred.raw_spam_score * 0.35), 2)
            risk_level = "High" if (ml_pred.raw_spam_score >= 0.85 and len(intents) > 0) else "Medium"
            classification = "Spam / Unsolicited"

    else:
        if medium_risk_urls or len(intents) >= 2:
            threat_category = "Needs Review"
            category_source = "insufficient_evidence"
            risk_level = "Needs Review"
            risk_score = 0.42
            classification = "Needs Review"
        else:
            threat_category = "Safe / Normal"
            category_source = "ml_baseline"
            risk_score = round(max(0.03, ml_pred.raw_spam_score * 0.4), 2)
            risk_level = "Low"
            classification = "Legitimate / Safe"

    # Forensic overrides (UPI/QR outgoing payment lures, Unicode spoofing, DLT/mobile sender mismatch)
    if upi_dissection:
        has_critical_upi = any(u.risk_level == "Critical" or u.lure_contradiction for u in upi_dissection)
        has_high_upi = any(u.risk_level == "High" for u in upi_dissection)
        if has_critical_upi:
            threat_category = "Financial Scam"
            risk_level = "Critical"
            risk_score = max(risk_score, 0.90)
            classification = "Suspicious / Scam Threat"
            category_source = "ml_and_rules" if ml_is_spam else "rule_indicator"
        elif threat_category in {"Safe / Normal", "Promotional", "Needs Review"}:
            threat_category = "Financial Scam"
            target_risk = "High" if has_high_upi else "Medium"
            if RISK_ORDER[target_risk] > RISK_ORDER.get(risk_level, 0):
                risk_level = target_risk
            risk_score = max(risk_score, 0.72 if has_high_upi else 0.55)
            classification = "Suspicious / Payment Request"
            category_source = "rule_indicator"

    if unicode_audit.has_obfuscation:
        high_severity_spoof = bool(
            unicode_audit.spoofed_brands
            or any(
                f.issue_type in {"userinfo_trick", "bidi_override", "mixed_script_homoglyph", "punycode"}
                for f in unicode_audit.findings
            )
            or unicode_audit.zero_width_count >= 2
        )
        if high_severity_spoof:
            if threat_category in {"Safe / Normal", "Promotional", "Needs Review"}:
                threat_category = "Phishing"
                classification = "Obfuscated / Spoofed Link Risk"
                category_source = "rule_indicator"
            if RISK_ORDER.get(risk_level, 0) < RISK_ORDER["High"]:
                risk_level = "High"
            risk_score = max(risk_score, 0.78)
            if unicode_audit.spoofed_brands and any(
                f.issue_type in {"userinfo_trick", "mixed_script_homoglyph"} for f in unicode_audit.findings
            ):
                risk_level = "Critical"
                risk_score = max(risk_score, 0.88)

    if sender_analysis.is_suspicious_mismatch:
        if threat_category in {"Safe / Normal", "Promotional", "Needs Review"}:
            threat_category = "Impersonation" if sender_analysis.claimed_entity else "Needs Review"
            classification = "Sender Impersonation Risk"
            category_source = "rule_indicator"
        target_sender_risk = (
            "High"
            if (sender_analysis.sender_type == "personal_mobile" and sender_analysis.claimed_entity)
            else "Medium"
        )
        if RISK_ORDER[target_sender_risk] > RISK_ORDER.get(risk_level, 0):
            risk_level = target_sender_risk
        risk_score = max(risk_score, 0.74 if target_sender_risk == "High" else 0.58)

    risk_score = round(min(1.0, risk_score), 2)

    official_channels = detect_official_verification_channels(
        message=eval_text,
        sender_id=sender_id,
        threat_category=threat_category,
        has_upi=bool(upi_dissection),
    )

    campaign_match = find_campaign_matches(
        message=eval_text,
        sender_id=sender_id,
        url_summary=url_summary,
        upi_items=upi_dissection,
        prior_flagged_records=prior_flagged_records,
        threat_category=threat_category,
    )

    # Build human-readable reasons
    reasons: list[str] = []
    if upi_dissection:
        for item in upi_dissection[:2]:
            reasons.append(f"[UPI / QR Forensic] {item.truth_statement}")
    if sender_analysis.is_suspicious_mismatch and sender_analysis.verdict_summary:
        reasons.append(f"[Sender Check] {sender_analysis.verdict_summary}")
    if unicode_audit.has_obfuscation and unicode_audit.findings:
        reasons.append(f"[Unicode Audit] {unicode_audit.findings[0].detail}")
    if campaign_match.has_match:
        reasons.append(f"[Campaign Match] {campaign_match.summary}")
    if rules_eval.scam_hits:
        for hit in rules_eval.scam_hits:
            reasons.append(f"[Rule: {hit.label}] {hit.description}")
    if url_summary.items:
        for u in url_summary.items:
            if u.risk_level in {"Medium", "High"}:
                reasons.append(f"[URL: {u.host}] {' '.join(u.findings)}")
            else:
                reasons.append(
                    f"[URL: {u.host}] Extracted URL passed local structural checks ({u.reputation_status.lower()})."
                )
    if intents:
        for intent in intents:
            reasons.append(
                f"[Intent: {intent.intent}] {intent.reason} (matched: {', '.join(intent.matched_phrases[:2])})"
            )
    if ml_is_spam:
        top_spam_tokens = [c.token for c in ml_pred.top_contributions if c.direction == "spam"][:4]
        tok_str = f" Key terms: {', '.join(top_spam_tokens)}." if top_spam_tokens else ""
        reasons.append(
            f"[ML Model] {ml_pred.model_display_name} flagged statistical similarity to spam "
            f"(score {ml_pred.raw_spam_score:.0%} >= threshold {ml_pred.threshold_used:.0%}).{tok_str}"
        )
    else:
        reasons.append(
            f"[ML Model] {ml_pred.model_display_name} scored below threshold "
            f"({ml_pred.raw_spam_score:.0%} < {ml_pred.threshold_used:.0%})."
        )
    if rules_eval.benign_context_hits:
        reasons.append(
            f"[Context Guard] Detected legitimate message cues ({', '.join(benign_labels)})."
        )

    # Collect concise, phrase-level highlight spans aligned to displayed message
    raw_spans: list[HighlightedSpan] = []
    rules_cfg = load_threat_rules(str(rules_path))

    for url_item in url_summary.items:
        m = re.search(re.escape(url_item.url), message)
        if m:
            raw_spans.append(
                HighlightedSpan(
                    start=m.start(),
                    end=m.end(),
                    text=m.group(0),
                    reason=f"URL ({url_item.risk_level} structural risk)",
                    severity=(
                        "high"
                        if url_item.risk_level == "High"
                        else "medium"
                        if url_item.risk_level == "Medium"
                        else "info"
                    ),
                )
            )

    if threat_category != "Safe / Normal":
        for hp in rules_cfg.get("highlight_phrases", []):
            for m in re.finditer(hp["pattern"], message, flags=re.IGNORECASE):
                raw_spans.append(
                    HighlightedSpan(
                        start=m.start(),
                        end=m.end(),
                        text=m.group(0),
                        reason=hp["reason"],
                        severity=hp.get("severity", "medium"),
                    )
                )

        # Only map eval_text rule hits directly when eval_text aligns with message
        if eval_text == message:
            for hit in rules_eval.scam_hits:
                if (hit.end - hit.start) <= 55:
                    raw_spans.append(
                        HighlightedSpan(
                            start=hit.start,
                            end=hit.end,
                            text=message[hit.start:hit.end],
                            reason=hit.label,
                            severity="critical" if hit.severity == "critical" else "high",
                        )
                    )
        for intent in intents:
            for phrase in intent.matched_phrases:
                if len(phrase) <= 55:
                    m = re.search(re.escape(phrase), message)
                    if m:
                        raw_spans.append(
                            HighlightedSpan(
                                start=m.start(),
                                end=m.end(),
                                text=m.group(0),
                                reason=f"Intent: {intent.intent}",
                                severity="medium",
                            )
                        )

    highlighted_spans = _deduplicate_overlapping_spans(raw_spans)

    if threat_category == "Safe / Normal":
        summary = "No common scam rules, credential traps, or suspicious URL patterns were detected."
    elif threat_category == "Promotional":
        summary = "Marketing or promotional cues were detected without high-risk fraud indicators."
    elif threat_category == "Needs Review":
        summary = "Signals are mixed or incomplete. Verify through an official channel before acting."
    else:
        signal_parts = []
        if upi_dissection:
            signal_parts.append("outgoing UPI/QR payment instruction")
        if unicode_audit.has_obfuscation:
            signal_parts.append("disguised lookalike/hidden characters")
        if sender_analysis.is_suspicious_mismatch:
            signal_parts.append("unverified or mismatched sender ID")
        if rule_models:
            signal_parts.append(rule_models[0].label)
        if url_summary.has_suspicious_urls:
            signal_parts.append("suspicious link structure")
        if intents and len(signal_parts) < 3:
            signal_parts.append(intents[0].intent.lower())
        if not signal_parts and ml_is_spam:
            signal_parts.append("spam language patterns")
        joined = ", ".join(dict.fromkeys(signal_parts[:3]))
        summary = f"Flagged as {threat_category} ({risk_level} risk) based on {joined}."

    recommendations = build_recommendations(
        threat_category=threat_category,
        risk_level=risk_level,
        rule_hits=rule_models,
        intents=intents,
        url_summary=url_summary,
        upi_items=upi_dissection,
        sender_analysis=sender_analysis,
        has_unicode_obfuscation=unicode_audit.has_obfuscation,
    )

    recovery_triage = build_recovery_triage(
        message=eval_text,
        threat_category=threat_category,
        sender_id=sender_id,
        url_summary=url_summary,
        upi_items=upi_dissection,
        has_unicode_obfuscation=unicode_audit.has_obfuscation,
    )

    return AnalyzeResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        message=message,
        sender_id=(sender_id.strip() if sender_id and sender_id.strip() else None),
        classification=classification,
        threat_category=threat_category,  # type: ignore[arg-type]
        category_source=category_source,  # type: ignore[arg-type]
        category_source_label=CATEGORY_SOURCE_LABELS[category_source],
        risk_level=risk_level,  # type: ignore[arg-type]
        risk_score=risk_score,
        summary=summary,
        ml_prediction=ml_pred,
        rule_indicators=rule_models,
        benign_context_matches=benign_labels,
        detected_intents=intents,
        url_analysis=url_summary,
        highlighted_spans=highlighted_spans,
        unicode_audit=unicode_audit,
        upi_dissection=upi_dissection,
        sender_analysis=sender_analysis,
        official_channels=official_channels,
        campaign_match=campaign_match,
        recovery_triage=recovery_triage,
        reasons=reasons,
        recommended_actions=recommendations,
        official_reporting_note=OFFICIAL_REPORTING_NOTE,
    )
