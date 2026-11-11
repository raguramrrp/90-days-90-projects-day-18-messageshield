"""Zero-network QR code decoder and upi://pay deep-link payment forensics."""

from __future__ import annotations

import io
import re
from typing import Literal
from urllib.parse import parse_qs, unquote, urlparse

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from src.schemas import UPIDissectionItem

UPI_URI_RE = re.compile(
    r"(?i)\b(?:upi://(?:pay|collect|mandate)|bhim://upi/pay|gpay://upi/pay|phonepe://pay)\?[^\s<>\"'\]\)]+"
)

PERSONAL_PSP_HANDLES = {
    "ybl",
    "oksbi",
    "okicici",
    "okaxis",
    "okhdfcbank",
    "paytm",
    "ibl",
    "axl",
    "upi",
    "apl",
    "yapl",
    "rapl",
    "pingpay",
    "waicici",
    "waaxis",
    "wahdfcbank",
    "wasbi",
    "ikwik",
    "barodampay",
    "fbl",
    "idfcbank",
    "jio",
}

TEST_PSP_HANDLES = {
    "exampleupi",
    "testupi",
    "invalidupi",
}

LURE_RECEIVE_RE = re.compile(
    r"(?i)\b(?:receive|get|claim|win|won|cashback|refund|reward|prize|lottery|bonus|credit(?:ed)?|salary)\b"
)

VPA_BAIT_KEYWORDS = (
    "cashback",
    "reward",
    "refund",
    "prize",
    "kyc",
    "bonus",
    "claim",
    "lottery",
    "helpdesk",
    "support",
    "care",
    "customs",
    "verify",
    "officer",
)


def extract_upi_uris(text: str) -> list[str]:
    """Extract unique upi:// payment/collect/mandate deep links from text."""
    if not text:
        return []
    seen: set[str] = set()
    results: list[str] = []
    for m in UPI_URI_RE.finditer(text):
        raw = m.group(0).rstrip(".,;:!?)']\"")
        if raw and raw not in seen:
            seen.add(raw)
            results.append(raw)
    return results


def _decode_qr_from_bgr(detector: cv2.QRCodeDetector, bgr: np.ndarray) -> list[str]:
    found: list[str] = []
    try:
        ok, decoded_info, _, _ = detector.detectAndDecodeMulti(bgr)
        if ok and decoded_info:
            for item in decoded_info:
                val = (item or "").strip()
                if val and val not in found:
                    found.append(val)
    except cv2.error:
        pass

    if not found:
        try:
            single, _, _ = detector.detectAndDecode(bgr)
            val = (single or "").strip()
            if val and val not in found:
                found.append(val)
        except cv2.error:
            pass
    return found


def decode_qr_codes_from_bytes(image_bytes: bytes) -> list[str]:
    """Decode any QR codes inside uploaded screenshot bytes without network calls."""
    if not image_bytes:
        return []
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            rgb = ImageOps.exif_transpose(img).convert("RGB")
            arr = np.array(rgb)
    except (UnidentifiedImageError, OSError, ValueError):
        return []

    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    detector = cv2.QRCodeDetector()

    # Pass 1: Direct detection on padded RGB screenshot (white border guards tight crops)
    padded_bgr = cv2.copyMakeBorder(
        bgr, 24, 24, 24, 24, cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )
    results = _decode_qr_from_bgr(detector, padded_bgr)
    if results:
        return results

    # Pass 2: Inverted brightness (handles dark-mode QR screenshots)
    if float(np.mean(gray)) < 115.0:
        inv = cv2.bitwise_not(padded_bgr)
        results = _decode_qr_from_bgr(detector, inv)
        if results:
            return results

    # Pass 3: Upscaled + Otsu thresholded binarization for small embedded QRs
    h, w = gray.shape
    scale = 2.0 if min(h, w) < 900 else 1.5
    upscaled = cv2.resize(
        gray,
        (int(w * scale), int(h * scale)),
        interpolation=cv2.INTER_NEAREST,
    )
    _, otsu = cv2.threshold(upscaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    padded_otsu = cv2.copyMakeBorder(
        cv2.cvtColor(otsu, cv2.COLOR_GRAY2BGR),
        28,
        28,
        28,
        28,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255),
    )
    results = _decode_qr_from_bgr(detector, padded_otsu)
    return results


def _format_amount_inr(amount_raw: str | None, currency: str) -> str:
    if not amount_raw:
        return ""
    cleaned = amount_raw.strip().replace(",", "")
    try:
        num = float(cleaned)
        if num.is_integer():
            formatted = f"{int(num):,}"
        else:
            formatted = f"{num:,.2f}"
    except ValueError:
        formatted = amount_raw.strip()
    symbol = "₹" if currency.upper() == "INR" else f"{currency.upper()} "
    return f"{symbol}{formatted}"


def inspect_upi_deep_link(
    raw_uri: str,
    message_context: str = "",
    source: Literal["message_text", "screenshot_qr"] = "message_text",
) -> UPIDissectionItem:
    """Dissect a upi://pay or collect/mandate deep link and state the exact payment outcome."""
    normalized_uri = raw_uri.strip()
    parsed_scheme_fixed = re.sub(
        r"(?i)^(?:bhim|gpay|phonepe)://(?:upi/)?",
        "upi://",
        normalized_uri,
    )
    parsed = urlparse(parsed_scheme_fixed)
    action_type = (parsed.netloc or parsed.path.lstrip("/") or "pay").lower()
    if "/" in action_type:
        action_type = action_type.rsplit("/", 1)[-1] or "pay"

    params = {k.lower(): (v[0] if v else "") for k, v in parse_qs(parsed.query, keep_blank_values=True).items()}

    payee_vpa = unquote(params.get("pa", "")).strip() or None
    payee_name = unquote(params.get("pn", "")).strip() or None
    amount_raw = unquote(params.get("am", "")).strip() or None
    currency = (unquote(params.get("cu", "")).strip() or "INR").upper()
    merchant_code = unquote(params.get("mc", "")).strip() or None
    transaction_note = unquote(params.get("tn", "")).strip() or None

    is_outgoing = action_type in {"pay", "collect", "mandate", "global"}
    handle_suffix = payee_vpa.rsplit("@", 1)[-1].lower() if (payee_vpa and "@" in payee_vpa) else ""
    is_test_handle = bool(handle_suffix and handle_suffix in TEST_PSP_HANDLES)
    is_personal_handle = bool(handle_suffix and (handle_suffix in PERSONAL_PSP_HANDLES or is_test_handle))

    combined_lure_text = " ".join(
        p for p in [message_context, payee_name or "", transaction_note or ""] if p
    )
    lure_contradiction = bool(is_outgoing and LURE_RECEIVE_RE.search(combined_lure_text))

    warnings: list[str] = []
    if lure_contradiction:
        warnings.append(
            "Payment Lure Contradiction: The message or note promises cashback/refund/receipt, but this UPI link authorizes an OUTGOING payment from your account."
        )

    if payee_vpa:
        local_part = payee_vpa.split("@", 1)[0].lower()
        if any(kw in local_part for kw in VPA_BAIT_KEYWORDS):
            warnings.append(
                f"Suspicious payee ID '{payee_vpa}' contains bait wording (e.g. cashback/reward/kyc/support) rarely used by genuine banks."
            )
    if is_personal_handle and (not merchant_code or merchant_code in {"0000", "0"}):
        if is_test_handle:
            warnings.append(
                f"Payee handle '@{handle_suffix}' is a synthetic test handle with no verified merchant code."
            )
        else:
            warnings.append(
                f"Payee handle '@{handle_suffix}' is a standard P2P handle with no verified merchant code."
            )
    if amount_raw:
        warnings.append(
            f"Pre-filled debit amount detected ({_format_amount_inr(amount_raw, currency)})."
        )
    elif is_outgoing:
        warnings.append(
            "Open-ended amount ('am' missing) — approving this lets the counterparty or prompt set any transfer amount."
        )
    if action_type == "mandate":
        warnings.append(
            "UPI AutoPay Mandate link — approving this authorizes recurring automatic debits from your bank account."
        )

    origin_label = "Scanning this QR code" if source == "screenshot_qr" else "Opening this UPI link"
    target_desc = payee_vpa or "an unknown payee"
    if payee_name:
        target_desc = f"{target_desc} ({payee_name})"
    amt_phrase = (
        f" of {_format_amount_inr(amount_raw, currency)}"
        if amount_raw
        else ""
    )
    truth_statement = (
        f"{origin_label} initiates an OUTGOING payment{amt_phrase} to {target_desc}. "
        "Entering your UPI PIN on a QR code or pay/collect link can NEVER deposit money into your bank account."
    )

    if lure_contradiction or action_type == "mandate" or (
        payee_vpa and any(kw in payee_vpa.lower() for kw in VPA_BAIT_KEYWORDS)
    ):
        risk_level: Literal["Medium", "High", "Critical"] = "Critical"
    elif is_personal_handle or bool(amount_raw):
        risk_level = "High"
    else:
        risk_level = "Medium"

    return UPIDissectionItem(
        raw_uri=raw_uri,
        source=source,
        action_type=action_type,
        payee_vpa=payee_vpa,
        payee_name=payee_name,
        amount=amount_raw,
        currency=currency,
        merchant_code=merchant_code,
        transaction_note=transaction_note,
        is_outgoing_transfer=is_outgoing,
        is_personal_handle=is_personal_handle,
        lure_contradiction=lure_contradiction,
        risk_level=risk_level,
        truth_statement=truth_statement,
        warnings=warnings,
    )


def dissect_all_upi_inputs(
    text: str,
    qr_payloads: list[str] | None = None,
) -> list[UPIDissectionItem]:
    """Dissect all upi:// links found in both message text and QR code payloads."""
    items: list[UPIDissectionItem] = []
    seen_uris: set[str] = set()

    for payload in qr_payloads or []:
        stripped = (payload or "").strip()
        if not stripped:
            continue
        if UPI_URI_RE.match(stripped) and stripped not in seen_uris:
            seen_uris.add(stripped)
            items.append(
                inspect_upi_deep_link(
                    stripped,
                    message_context=text,
                    source="screenshot_qr",
                )
            )

    for uri in extract_upi_uris(text):
        if uri not in seen_uris:
            seen_uris.add(uri)
            items.append(
                inspect_upi_deep_link(
                    uri,
                    message_context=text,
                    source="message_text",
                )
            )
    return items
