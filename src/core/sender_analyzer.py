"""Indian TRAI DLT sender-header decoder and offline official verification directory."""

from __future__ import annotations

import re
from typing import Any

from src.schemas import OfficialVerificationChannel, SenderAnalysis

TRAI_OPERATORS: dict[str, str] = {
    "A": "Bharti Airtel",
    "B": "BSNL",
    "C": "V-CON",
    "D": "Aircel / Dishnet",
    "J": "Reliance Jio",
    "M": "MTNL",
    "Q": "Quadrant",
    "R": "Reliance Communications",
    "T": "Tata Teleservices",
    "V": "Vodafone Idea (Vi)",
}

TRAI_CIRCLES: dict[str, str] = {
    "A": "Andhra Pradesh & Telangana",
    "B": "Bihar & Jharkhand",
    "C": "Chennai",
    "D": "Delhi NCR",
    "E": "Uttar Pradesh (East)",
    "G": "Gujarat",
    "H": "Haryana",
    "I": "Himachal Pradesh",
    "J": "Jammu & Kashmir",
    "K": "Kolkata",
    "L": "Kerala",
    "M": "Mumbai",
    "N": "North East",
    "O": "Odisha",
    "P": "Punjab",
    "R": "Rajasthan",
    "S": "Assam",
    "T": "Tamil Nadu",
    "U": "Uttar Pradesh (West)",
    "V": "Pan-India / Virtual",
    "W": "Maharashtra & Goa",
    "X": "Karnataka",
    "Y": "Madhya Pradesh & Chhattisgarh",
    "Z": "West Bengal",
}

TRAI_SUFFIX_LABELS: dict[str, str] = {
    "S": "Service / Alert (-S)",
    "T": "Transactional / OTP (-T)",
    "P": "Promotional (-P)",
    "G": "Government (-G)",
}

OFFICIAL_ENTITIES: list[dict[str, Any]] = [
    {
        "key": "sbi",
        "entity": "State Bank of India (SBI)",
        "patterns": [r"\bsbi\b", r"\byono\b", r"\bonlinesbi\b", r"\bsbicrd\b"],
        "official_domain": "sbi.co.in",
        "helplines": ["1800 1234", "1800 2100", "1800 11 1109"],
        "official_headers": ["SBIINB", "SBICRD", "ATMSBI", "SBIPSG", "CBSBI", "SBYONO"],
        "verify_instruction": "Close this SMS. Open the YONO SBI app directly or type sbi.co.in in your browser, or call toll-free 1800 1234 / 1800 2100.",
    },
    {
        "key": "hdfc",
        "entity": "HDFC Bank",
        "patterns": [r"\bhdfc\b", r"\bhdfcbank\b", r"\bhdfcbk\b", r"\bhdfccc\b"],
        "official_domain": "hdfcbank.com",
        "helplines": ["1800 1600", "1800 2600", "1800 202 6161"],
        "official_headers": ["HDFCBK", "HDFCCC", "HDFCAL"],
        "verify_instruction": "Do not tap SMS links. Open the official HDFC Bank MobileBanking app or call 1800 1600 / 1800 2600 directly.",
    },
    {
        "key": "icici",
        "entity": "ICICI Bank",
        "patterns": [r"\bicici\b", r"\biMobile\b", r"\bicicibank\b"],
        "official_domain": "icicibank.com",
        "helplines": ["1800 1080"],
        "official_headers": ["ICICIB", "ICICIC", "ICICIA"],
        "verify_instruction": "Check account alerts inside the official iMobile Pay app or call 1800 1080.",
    },
    {
        "key": "axis",
        "entity": "Axis Bank",
        "patterns": [r"\baxis\s*bank\b", r"\baxisbk\b"],
        "official_domain": "axisbank.com",
        "helplines": ["1800 209 5577", "1800 419 0097"],
        "official_headers": ["AXISBK", "AXISCC"],
        "verify_instruction": "Open the official Axis Mobile app directly or dial 1800 209 5577 to verify card or KYC status.",
    },
    {
        "key": "paytm",
        "entity": "Paytm / Paytm Payments Bank",
        "patterns": [r"\bpaytm\b"],
        "official_domain": "paytm.com",
        "helplines": ["0120-4440440"],
        "official_headers": ["PAYTMB", "PAYTM", "PTMWLT"],
        "verify_instruction": "Open the Paytm app directly and check '24x7 Help & Support' — never approve KYC or cashback via browser links.",
    },
    {
        "key": "phonepe",
        "entity": "PhonePe",
        "patterns": [r"\bphonepe\b"],
        "official_domain": "phonepe.com",
        "helplines": ["080-6872 7374", "022-6872 7374"],
        "official_headers": ["PHONPE", "PHNPAY"],
        "verify_instruction": "Check pending requests and help tickets solely inside your PhonePe app.",
    },
    {
        "key": "indiapost",
        "entity": "India Post",
        "patterns": [r"\bindia\s*post\b", r"\bspeed\s*post\b", r"\bindpst\b", r"\bdopind\b"],
        "official_domain": "indiapost.gov.in",
        "helplines": ["1800 266 6868"],
        "official_headers": ["INDPST", "DOPIND", "IPBMSG"],
        "verify_instruction": "Track consignment numbers directly at indiapost.gov.in — India Post does not ask for Rs.25 redelivery fees over SMS links.",
    },
    {
        "key": "uidai",
        "entity": "UIDAI (Aadhaar)",
        "patterns": [r"\baadhaar\b", r"\buidai\b"],
        "official_domain": "uidai.gov.in",
        "helplines": ["1947"],
        "official_headers": ["UIDAI", "AADHAR"],
        "verify_instruction": "Verify Aadhaar updates only on myaadhaar.uidai.gov.in or by calling toll-free helpline 1947.",
    },
    {
        "key": "epfo",
        "entity": "EPFO (Provident Fund)",
        "patterns": [r"\bepfo\b", r"\bpf\s*account\b", r"\bepfindia\b"],
        "official_domain": "epfindia.gov.in",
        "helplines": ["14470", "1800 118 005"],
        "official_headers": ["EPFOHO", "EPFIND"],
        "verify_instruction": "Verify PF/UAN status directly on epfindia.gov.in or call toll-free 14470 / 1800 118 005.",
    },
    {
        "key": "incometax",
        "entity": "Income Tax Department",
        "patterns": [r"\bincome\s*tax\b", r"\btax\s*refund\b", r"\bitd\b", r"\bpan\s*card\b"],
        "official_domain": "incometax.gov.in",
        "helplines": ["1800 180 1961", "1800 103 0025"],
        "official_headers": ["ITDIND", "INCMTX", "CPCREF"],
        "verify_instruction": "Check tax refund or PAN notices strictly inside the e-Filing portal (incometax.gov.in) or call 1800 180 1961.",
    },
    {
        "key": "electricity",
        "entity": "Electricity Utility / DISCOM",
        "patterns": [r"\bbescom\b", r"\belectricity\b", r"\bpower\s+will\s+be\s+disconnected\b", r"\bmeter\b"],
        "official_domain": "bbps / state-discom.gov.in",
        "helplines": ["1912"],
        "official_headers": ["BESCOM", "TNEB", "MSEDCL", "DISCOM", "BYPL", "BRPL"],
        "verify_instruction": "Call National Electricity Helpline 1912 or check your bill inside your official state DISCOM portal / BBPS app — never call personal 10-digit numbers.",
    },
    {
        "key": "rbi",
        "entity": "Reserve Bank of India (RBI)",
        "patterns": [r"\brbi\b", r"\breserve\s*bank\b"],
        "official_domain": "rbi.org.in",
        "helplines": ["14448", "14440"],
        "official_headers": ["RBISAY", "RBIORG"],
        "verify_instruction": "RBI never calls or texts individuals for KYC fees or prize release. Verify advisories at sachet.rbi.org.in or call 14440.",
    },
    {
        "key": "samplebank",
        "entity": "SampleBank (Demo Institution)",
        "patterns": [r"\bsample\s*bank\b", r"\bdemo\s*bank\b", r"\bsamplebank\b", r"\bdemobank\b"],
        "official_domain": "samplebank.example",
        "helplines": ["1800-000-0000"],
        "official_headers": ["DMOBNK", "SMPBNK"],
        "verify_instruction": "Verify KYC or card status only inside the official SampleBank app or website (samplebank.example) — never tap SMS links.",
    },
    {
        "key": "sampleparcel",
        "entity": "Sample Parcel Service (Demo)",
        "patterns": [r"\bsample\s*parcel\b", r"\bdemo\s*parcel\b", r"\bparcel\s*service\b"],
        "official_domain": "sampleparcel.example",
        "helplines": ["1800-000-0001"],
        "official_headers": ["DMOPRC", "SMPPRC"],
        "verify_instruction": "Track your demo consignment directly at sampleparcel.example — never pay redelivery fees through unknown SMS links.",
    },
]

OFFICIAL_DOMAIN_BY_KEY = {e["key"]: e for e in OFFICIAL_ENTITIES}

PERSONAL_MOBILE_RE = re.compile(r"^(?:\+?91[\s-]?)?((?:[6-9]\d{9}|00000\d{5}))$")
INTERNATIONAL_NUM_RE = re.compile(r"^\+\d{7,15}$")
DLT_HEADER_RE = re.compile(r"^([A-Z]{2})-([A-Z0-9]{3,9})(?:-([STPG]))?$")
SHORTCODE_ALPHA_RE = re.compile(r"^[A-Z0-9]{3,9}$")
OFFICIAL_CLAIM_WORDS_RE = re.compile(
    r"(?i)\b(?:bank|sample\s*bank|demo\s*bank|samplebank|demobank|kyc|sbi|hdfc|icici|axis|paytm|phonepe|electricity|power|discom|"
    r"india\s*post|parcel|customs|aadhaar|uidai|epfo|income\s*tax|rbi|government|police|cyber)\b"
)


def _match_claimed_entities(text: str, sender_clean: str = "") -> list[dict[str, Any]]:
    combined = f"{sender_clean} {text}".strip()
    matched: list[dict[str, Any]] = []
    for item in OFFICIAL_ENTITIES:
        if any(re.search(pat, combined, flags=re.IGNORECASE) for pat in item["patterns"]):
            matched.append(item)
    return matched


def extract_sender_from_ocr_lines(raw_ocr_text: str) -> str | None:
    """Extract likely SMS header / phone number from screenshot top lines when visible."""
    if not raw_ocr_text:
        return None
    lines = [ln.strip() for ln in raw_ocr_text.splitlines() if ln.strip()]
    for line in lines[:3]:
        # Handle simulated or UI headers like 'Messages | VK-DMOKYC' or 'From: AD-DMOBNK-T'
        pipe_match = re.search(
            r"(?:Messages|SMS|From)\s*[|:\-]+\s*([+A-Z0-9][+A-Z0-9\-\s]{2,20})",
            line,
            flags=re.IGNORECASE,
        )
        if pipe_match:
            candidate = re.sub(r"\s+", " ", pipe_match.group(1)).strip(" |:-")
            upper_cand = candidate.upper()
            if (
                DLT_HEADER_RE.match(upper_cand)
                or PERSONAL_MOBILE_RE.match(candidate.replace(" ", ""))
                or INTERNATIONAL_NUM_RE.match(candidate.replace(" ", ""))
                or SHORTCODE_ALPHA_RE.match(upper_cand)
            ):
                return upper_cand if not candidate.startswith("+") else candidate

        # Handle standalone top line header e.g. 'VK-DMOKYC' or '+91 00000 00001'
        compact = line.replace(" ", "")
        upper_line = line.upper().strip()
        if DLT_HEADER_RE.match(upper_line):
            return upper_line
        if PERSONAL_MOBILE_RE.match(compact):
            return line
    return None


def analyze_sender_id(sender_id: str | None, message: str) -> SenderAnalysis:
    """Decode TRAI DLT header structure or flag mobile-number / category mismatches."""
    raw = (sender_id or "").strip()
    if not raw:
        return SenderAnalysis(provided=False, sender_type="none")

    compact = re.sub(r"[\s-]+", "", raw)
    upper = re.sub(r"\s+", "", raw).upper()
    claimed_entities = _match_claimed_entities(message, upper)
    claimed_name = claimed_entities[0]["entity"] if claimed_entities else None
    looks_official_claim = bool(claimed_entities or OFFICIAL_CLAIM_WORDS_RE.search(message))

    findings: list[str] = []
    suspicious_mismatch = False

    # 1. Personal 10-digit Indian mobile or raw phone number
    mob_match = PERSONAL_MOBILE_RE.match(compact)
    if mob_match or INTERNATIONAL_NUM_RE.match(compact):
        if looks_official_claim:
            suspicious_mismatch = True
            entity_note = claimed_name or "an official institution/utility"
            findings.append(
                f"Message arrives from a regular mobile number ({raw}) while claiming {entity_note}. Official banks, DISCOMs, and govt agencies under TRAI rules must use registered alphabetic headers."
            )
            verdict = f"High-Risk Mismatch: Personal number impersonating {entity_note}."
        else:
            findings.append(
                f"Sender '{raw}' is a standard telephone/mobile number, not a registered TRAI DLT service header."
            )
            verdict = "Sent from a regular mobile/phone number (unverified sender)."

        return SenderAnalysis(
            provided=True,
            raw_sender=raw,
            sender_type="personal_mobile",
            claimed_entity=claimed_name,
            is_suspicious_mismatch=suspicious_mismatch,
            verdict_summary=verdict,
            findings=findings,
        )

    # 2. Structured Indian TRAI DLT Header: <Op><Circle>-<CoreHeader>(-<S/T/P/G>)
    dlt_match = DLT_HEADER_RE.match(upper)
    if dlt_match:
        prefix, header_code, suffix = dlt_match.groups()
        op_code, circle_code = prefix[0], prefix[1]
        operator_name = TRAI_OPERATORS.get(op_code, f"Registered Carrier ({op_code})")
        circle_name = TRAI_CIRCLES.get(circle_code, f"Telecom Circle ({circle_code})")
        category_label = (
            TRAI_SUFFIX_LABELS.get(suffix)
            if suffix
            else "Unspecified Category (legacy/short format)"
        )

        findings.append(
            f"TRAI DLT Routing: {operator_name} · {circle_name} (Header: {header_code})."
        )
        if suffix:
            findings.append(f"Declared Message Type: {category_label}.")

        if suffix == "P" and looks_official_claim:
            suspicious_mismatch = True
            findings.append(
                "Type Mismatch: Marked '-P' (Promotional) even though the text threatens urgent KYC, bank block, or govt action."
            )

        matched_official = False
        for ent in claimed_entities:
            known_headers = set(ent["official_headers"])
            if header_code in known_headers:
                matched_official = True
                findings.append(
                    f"Header '{header_code}' aligns with a known {ent['entity']} header format (still check links independently)."
                )
                break
            else:
                suspicious_mismatch = True
                findings.append(
                    f"Header '{header_code}' does not match {ent['entity']}'s common registered headers ({', '.join(ent['official_headers'][:4])}). Verify outside this SMS."
                )
                break

        if suspicious_mismatch:
            verdict = f"Suspicious Sender Header ({upper}) — does not match typical official records."
        elif matched_official and suffix in {"T", "S", "G"}:
            verdict = f"Registered {category_label} header routed via {operator_name}."
        else:
            verdict = f"DLT Header decoded ({operator_name} · {circle_name})."

        return SenderAnalysis(
            provided=True,
            raw_sender=raw,
            sender_type="trai_dlt_header",
            operator_name=operator_name,
            circle_name=circle_name,
            header_code=header_code,
            category_suffix=suffix,
            category_label=category_label,
            claimed_entity=claimed_name,
            is_suspicious_mismatch=suspicious_mismatch,
            verdict_summary=verdict,
            findings=findings,
        )

    # 3. Bare alphanumeric shortcode (e.g. HDFCBK, SBIKYC)
    if SHORTCODE_ALPHA_RE.match(upper):
        findings.append(
            f"Alphanumeric shortcode '{upper}' without full TRAI <Op><Circle>-<Header>-<Type> prefix (common when copied without full SMS metadata)."
        )
        for ent in claimed_entities:
            if upper in set(ent["official_headers"]):
                findings.append(
                    f"Shortcode '{upper}' matches common {ent['entity']} header pattern."
                )
            else:
                suspicious_mismatch = True
                findings.append(
                    f"Shortcode '{upper}' differs from typical {ent['entity']} headers ({', '.join(ent['official_headers'][:4])})."
                )
            break

        verdict = (
            f"Unverified shortcode '{upper}' for {claimed_name}."
            if suspicious_mismatch
            else f"Alphanumeric sender shortcode ({upper})."
        )
        return SenderAnalysis(
            provided=True,
            raw_sender=raw,
            sender_type="shortcode_or_alpha",
            header_code=upper,
            claimed_entity=claimed_name,
            is_suspicious_mismatch=suspicious_mismatch,
            verdict_summary=verdict,
            findings=findings,
        )

    # 4. Fallback unknown string
    return SenderAnalysis(
        provided=True,
        raw_sender=raw,
        sender_type="unknown",
        claimed_entity=claimed_name,
        is_suspicious_mismatch=looks_official_claim,
        verdict_summary="Unrecognized sender format — verify independently through official apps.",
        findings=[f"Sender '{raw}' could not be mapped to a standard TRAI DLT header format."],
    )


def detect_official_verification_channels(
    message: str,
    sender_id: str | None = None,
    threat_category: str = "Safe / Normal",
    has_upi: bool = False,
) -> list[OfficialVerificationChannel]:
    """Return offline official helplines/websites to verify claims safely without links."""
    matched_entities = _match_claimed_entities(message, (sender_id or "").upper())
    channels: list[OfficialVerificationChannel] = []

    is_threat = threat_category not in {"Safe / Normal", "Promotional"} or has_upi
    if not is_threat and not matched_entities:
        return []

    # Show recognized institutional channels whenever impersonation or risky message involves them
    if is_threat:
        for ent in matched_entities[:2]:
            channels.append(
                OfficialVerificationChannel(
                    entity=ent["entity"],
                    official_domain=ent["official_domain"],
                    helplines=list(ent["helplines"]),
                    official_headers=list(ent["official_headers"]),
                    verify_instruction=ent["verify_instruction"],
                )
            )
    elif sender_id and matched_entities:
        # Even for Safe / Normal, if user explicitly provided a bank sender ID, no need to clutter unless desired;
        # keep Safe / Normal clean unless sender mismatch exists.
        return []

    # Always offer verified India Cyber Fraud / Chakshu helpline on risky messages without noise
    if is_threat and len(channels) < 3:
        if any(kw in message.lower() for kw in ("upi", "bank", "kyc", "otp", "card", "money", "rs", "inr", "₹")) or has_upi or threat_category in {
            "Financial Scam",
            "Phishing",
            "OTP / Credential Theft",
            "Impersonation",
        }:
            channels.append(
                OfficialVerificationChannel(
                    entity="National Cyber Crime Helpline / Chakshu",
                    official_domain="cybercrime.gov.in · sancharsaathi.gov.in",
                    helplines=["1930"],
                    official_headers=[],
                    verify_instruction="Call 1930 immediately if money moved, or report unsolicited fraud SMS/calls on Sanchar Saathi (Chakshu).",
                )
            )

    return channels[:3]
