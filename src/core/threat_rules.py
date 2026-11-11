"""Modular rule loader and India-focused threat pattern evaluator."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config import RULES_PATH


@dataclass(frozen=True)
class MatchedRuleHit:
    rule_id: str
    label: str
    category: str
    severity: str
    weight: float
    description: str
    matched_text: str
    start: int
    end: int


@dataclass(frozen=True)
class RulesEvaluation:
    scam_hits: list[MatchedRuleHit]
    promotional_hits: list[tuple[str, int, int]]
    benign_context_hits: list[dict[str, Any]]


@lru_cache(maxsize=4)
def load_threat_rules(rules_path_str: str = str(RULES_PATH)) -> dict[str, Any]:
    path = Path(rules_path_str)
    if not path.exists():
        raise FileNotFoundError(f"Threat rules file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _matches_any(patterns: list[str], text: str) -> bool:
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE | re.DOTALL):
            return True
    return False


def evaluate_threat_rules(
    text: str,
    rules_path: Path = RULES_PATH,
) -> RulesEvaluation:
    """Evaluate modular India scam rules, promo cues, and benign context guards."""
    config = load_threat_rules(str(rules_path))

    scam_hits: list[MatchedRuleHit] = []
    for rule in config.get("india_scam_rules", []):
        excluded = rule.get("excluded_if_matches", [])
        if excluded and _matches_any(excluded, text):
            continue

        for pattern in rule.get("patterns", []):
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                scam_hits.append(
                    MatchedRuleHit(
                        rule_id=rule["id"],
                        label=rule["label"],
                        category=rule["category"],
                        severity=rule["severity"],
                        weight=float(rule.get("weight", 0.35)),
                        description=rule["description"],
                        matched_text=match.group(0).strip(),
                        start=match.start(),
                        end=match.end(),
                    )
                )
                break  # One match per rule avoids duplicate inflation

    promo_hits: list[tuple[str, int, int]] = []
    for pattern in config.get("promotional_patterns", []):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            promo_hits.append((match.group(0).strip(), match.start(), match.end()))

    benign_hits: list[dict[str, Any]] = []
    for ctx in config.get("benign_context_patterns", []):
        match = re.search(ctx["pattern"], text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            benign_hits.append(
                {
                    "id": ctx["id"],
                    "label": ctx["label"],
                    "matched_text": match.group(0).strip(),
                    "start": match.start(),
                    "end": match.end(),
                }
            )

    return RulesEvaluation(
        scam_hits=scam_hits,
        promotional_hits=promo_hits,
        benign_context_hits=benign_hits,
    )
