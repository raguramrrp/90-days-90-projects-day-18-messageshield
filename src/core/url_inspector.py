"""Offline structural URL inspector (never opens or fetches extracted URLs)."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.config import DEFAULT_URL_REPUTATION_PROVIDER, RULES_PATH, VIRUSTOTAL_API_KEY
from src.core.threat_rules import load_threat_rules
from src.ml.preprocessing import extract_urls
from src.schemas import URLInspectionItem, URLSummary

IPV4_HOST_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def _normalize_for_parse(raw_url: str) -> str:
    lower = raw_url.lower()
    if lower.startswith(("http://", "https://")):
        return raw_url
    return f"http://{raw_url}"


def _host_matches_official(host: str, official_domains: list[str]) -> bool:
    for official in official_domains:
        if host == official or host.endswith(f".{official}"):
            return True
    return False


def inspect_urls(
    text: str,
    reputation_mode: str | None = None,
    rules_path: Path = RULES_PATH,
) -> URLSummary:
    """Extract and structurally inspect URLs without performing network fetches."""
    raw_urls = extract_urls(text)
    config = load_threat_rules(str(rules_path))
    url_rules = config.get("url_rules", {})

    shorteners = set(url_rules.get("shortener_domains", []))
    suspicious_tlds = set(url_rules.get("suspicious_tlds", []))
    suspicious_keywords = url_rules.get("suspicious_keywords_in_url", [])
    suspicious_params = set(url_rules.get("suspicious_query_params", []))
    brand_targets: dict[str, list[str]] = url_rules.get("brand_lookalike_targets", {})

    mode = reputation_mode or DEFAULT_URL_REPUTATION_PROVIDER
    has_external_key = bool(VIRUSTOTAL_API_KEY) and mode == "external_configured"

    if has_external_key:
        reputation_notice = (
            "External URL reputation provider configured, but live lookups only run on "
            "explicit user submission; absence from a blocklist never guarantees safety."
        )
    else:
        reputation_notice = (
            "URL inspection is structural only (no external reputation service configured). "
            "Do not treat an unlisted link as safe."
        )

    items: list[URLInspectionItem] = []
    any_suspicious = False

    for raw_url in raw_urls:
        has_explicit_scheme = raw_url.lower().startswith(("http://", "https://"))
        normalized = _normalize_for_parse(raw_url)
        parsed = urlparse(normalized)
        scheme = parsed.scheme.lower() if has_explicit_scheme else "unspecified"
        raw_netloc = parsed.netloc.lower()
        host = (parsed.hostname or "").lower().strip(".")

        findings: list[str] = []
        risk_score = 0.0

        # 1. Userinfo deception (@ in authority section)
        if "@" in raw_netloc:
            findings.append("Contains '@' userinfo trick that masks the true destination host.")
            risk_score += 0.45

        # 2. IP-address host check
        is_ip = False
        if host:
            try:
                ipaddress.ip_address(host)
                is_ip = True
            except ValueError:
                is_ip = bool(IPV4_HOST_RE.match(host))
        if is_ip:
            findings.append("Uses a raw IP address instead of a verifiable domain name.")
            risk_score += 0.45

        # 3. URL shortener check
        is_shortened = host in shorteners or any(host.endswith(f".{s}") for s in shorteners)
        if is_shortened:
            findings.append("Uses a URL shortener that hides the true destination.")
            risk_score += 0.30

        # 4. Suspicious / commonly abused TLD check
        tld = host.rsplit(".", 1)[-1] if "." in host else ""
        has_suspicious_tld = tld in suspicious_tlds
        if has_suspicious_tld:
            findings.append(f"Uses a high-abuse top-level domain (.{tld}).")
            risk_score += 0.25

        # 5. Punycode / IDN homograph indicator
        if "xn--" in host:
            findings.append("Contains punycode (xn--) encoding often used in homograph lookalikes.")
            risk_score += 0.35

        # 6. Lookalike / brand impersonation domain check
        is_lookalike = False
        lookalike_target: str | None = None
        if host and not is_ip and not is_shortened:
            for brand, official_list in brand_targets.items():
                if brand in host and not _host_matches_official(host, official_list):
                    is_lookalike = True
                    lookalike_target = brand.upper()
                    findings.append(
                        f"Domain mentions '{brand}' but is not an official {brand.upper()} domain ({', '.join(official_list)})."
                    )
                    risk_score += 0.45
                    break

        # 7. Unusual subdomain depth or hyphenation
        if host and not is_ip:
            dot_count = host.count(".")
            hyphen_count = host.count("-")
            if dot_count >= 3:
                findings.append("Excessive subdomain nesting detected.")
                risk_score += 0.15
            if hyphen_count >= 2:
                findings.append("Multiple hyphens in domain name (common in disposable phishing domains).")
                risk_score += 0.15

        # 8. Unencrypted HTTP scheme
        if scheme == "http":
            findings.append("Uses unencrypted http:// rather than https://.")
            risk_score += 0.15

        # 9. Suspicious path keywords & query parameters
        lower_path_query = f"{parsed.path}?{parsed.query}".lower()
        matched_url_kw = [kw for kw in suspicious_keywords if kw in lower_path_query or kw in host]
        if matched_url_kw and not (
            any(_host_matches_official(host, offs) for offs in brand_targets.values())
        ):
            findings.append(
                f"URL contains sensitive action keywords ({', '.join(matched_url_kw[:4])})."
            )
            risk_score += 0.20

        query_keys = {k.lower() for k in parse_qs(parsed.query).keys()}
        matched_params = sorted(query_keys & suspicious_params)
        has_suspicious_params = len(matched_params) > 0
        if has_suspicious_params:
            findings.append(
                f"Contains sensitive/redirect query parameters ({', '.join(matched_params)})."
            )
            risk_score += 0.20

        risk_score = round(min(1.0, risk_score), 2)
        if risk_score >= 0.45 or is_ip or is_lookalike:
            risk_level = "High"
            any_suspicious = True
        elif risk_score >= 0.20 or is_shortened or has_suspicious_tld:
            risk_level = "Medium"
            any_suspicious = True
        else:
            risk_level = "Low"
            if not findings:
                findings.append(
                    "No structural anomalies detected locally; verify sender identity before opening."
                )

        items.append(
            URLInspectionItem(
                url=raw_url,
                normalized_url=normalized,
                host=host or raw_url,
                scheme=scheme,
                is_shortened=is_shortened,
                is_ip_address=is_ip,
                has_suspicious_tld=has_suspicious_tld,
                is_lookalike_domain=is_lookalike,
                lookalike_target=lookalike_target,
                has_suspicious_params=has_suspicious_params,
                risk_score=risk_score,
                risk_level=risk_level,
                findings=findings,
                reputation_status=(
                    "Structural check only (no live reputation lookup performed)"
                    if not has_external_key
                    else "External reputation provider configured (manual lookup available)"
                ),
            )
        )

    return URLSummary(
        count=len(items),
        has_suspicious_urls=any_suspicious,
        reputation_mode="external_configured" if has_external_key else "local_only",
        reputation_notice=reputation_notice,
        items=items,
    )
