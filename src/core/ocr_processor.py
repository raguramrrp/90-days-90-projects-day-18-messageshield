"""Screenshot OCR & QR payload extraction using OpenCV/Pillow and Tesseract."""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError

from src.config import ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_MB, resolve_tesseract_path
from src.core.sender_analyzer import extract_sender_from_ocr_lines
from src.core.upi_dissector import decode_qr_codes_from_bytes, dissect_all_upi_inputs
from src.ml.preprocessing import normalize_whitespace
from src.schemas import OCRResponse


def get_ocr_status() -> tuple[bool, str]:
    """Return whether Tesseract OCR binary is available and its version string."""
    exe = resolve_tesseract_path()
    if not exe:
        return False, "Tesseract OCR not found"
    try:
        pytesseract.pytesseract.tesseract_cmd = exe
        version = str(pytesseract.get_tesseract_version())
        return True, f"Tesseract {version}"
    except Exception as exc:
        return False, f"Tesseract error: {exc}"


def _preprocess_screenshot(pil_image: Image.Image) -> Image.Image:
    """Convert screenshot to high-contrast grayscale suitable for SMS OCR."""
    rgb = ImageOps.exif_transpose(pil_image).convert("RGB")
    arr = np.array(rgb)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Upscale smaller mobile screenshots so small font glyphs remain legible
    height, width = gray.shape
    if min(height, width) < 900:
        scale = 2.0 if min(height, width) < 550 else 1.5
        gray = cv2.resize(
            gray,
            (int(width * scale), int(height * scale)),
            interpolation=cv2.INTER_CUBIC,
        )

    # If dark-mode screenshot (dark background, light text), invert for Tesseract
    if float(np.mean(gray)) < 115.0:
        gray = cv2.bitwise_not(gray)

    denoised = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


def extract_text_from_screenshot(
    image_bytes: bytes,
    filename: str = "screenshot.png",
) -> OCRResponse:
    """Extract editable text, sender metadata, and QR payloads from a screenshot."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return OCRResponse(
            success=False,
            extracted_text="",
            character_count=0,
            word_count=0,
            engine="validation",
            message=f"Unsupported image format '{ext or 'unknown'}'. Upload PNG, JPG, WEBP, BMP, or TIFF.",
        )

    if not image_bytes:
        return OCRResponse(
            success=False,
            extracted_text="",
            character_count=0,
            word_count=0,
            engine="validation",
            message="Uploaded image file is empty.",
        )

    max_bytes = MAX_IMAGE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        return OCRResponse(
            success=False,
            extracted_text="",
            character_count=0,
            word_count=0,
            engine="validation",
            message=f"Image exceeds the {MAX_IMAGE_MB} MB upload limit.",
        )

    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.load()
            processed = _preprocess_screenshot(img)
    except (UnidentifiedImageError, OSError, ValueError):
        return OCRResponse(
            success=False,
            extracted_text="",
            character_count=0,
            word_count=0,
            engine="validation",
            message="Could not decode the uploaded file as a valid image.",
        )

    # Zero-network OpenCV QR code detection (runs even before OCR text extraction)
    qr_payloads = decode_qr_codes_from_bytes(image_bytes)

    exe = resolve_tesseract_path()
    raw_text = ""
    cleaned = ""
    detected_sender: str | None = None
    version_str = "QR-only"

    if exe:
        pytesseract.pytesseract.tesseract_cmd = exe
        try:
            version_str = str(pytesseract.get_tesseract_version())
            raw_text = pytesseract.image_to_string(processed, config="--oem 3 --psm 6")
            cleaned = normalize_whitespace(raw_text)
            if len(cleaned) < 4:
                raw_fallback = pytesseract.image_to_string(processed, config="--oem 3 --psm 3")
                fallback_clean = normalize_whitespace(raw_fallback)
                if len(fallback_clean) > len(cleaned):
                    raw_text = raw_fallback
                    cleaned = fallback_clean
            detected_sender = extract_sender_from_ocr_lines(raw_text)
        except Exception as exc:
            if not qr_payloads:
                return OCRResponse(
                    success=False,
                    extracted_text="",
                    character_count=0,
                    word_count=0,
                    engine="Tesseract OCR",
                    message=f"OCR processing failed: {exc}",
                )
    elif not qr_payloads:
        return OCRResponse(
            success=False,
            extracted_text="",
            character_count=0,
            word_count=0,
            engine="unavailable",
            message="Tesseract OCR engine is not installed or configured on this system. Paste the message text manually instead.",
        )

    upi_previews = dissect_all_upi_inputs(cleaned, qr_payloads=qr_payloads)
    words = [w for w in cleaned.split() if any(ch.isalnum() for ch in w)]

    if not cleaned and not qr_payloads:
        return OCRResponse(
            success=False,
            extracted_text="",
            character_count=0,
            word_count=0,
            engine=f"Tesseract {version_str}" if exe else "OpenCV QR",
            message="No readable text or QR code could be extracted from this screenshot. Try cropping closer to the message or pasting the text manually.",
        )

    if len(words) == 0 and qr_payloads:
        # Pure QR screenshot with sparse/no caption
        cleaned = f"QR code payload detected: {qr_payloads[0]}"
        words = [w for w in cleaned.split() if any(ch.isalnum() for ch in w)]

    warnings = [
        "Verify the extracted text for OCR typos before running analysis.",
        "Links and QR codes detected in screenshots are never opened automatically.",
    ]
    if qr_payloads:
        warnings.append(
            f"Decoded {len(qr_payloads)} QR code payload(s) locally inside the screenshot."
        )

    engine_label = (
        f"Tesseract {version_str} + OpenCV QR"
        if (exe and qr_payloads)
        else (f"Tesseract {version_str}" if exe else "OpenCV QR")
    )

    return OCRResponse(
        success=True,
        extracted_text=cleaned,
        detected_sender=detected_sender,
        qr_payloads=qr_payloads,
        upi_previews=upi_previews,
        character_count=len(cleaned),
        word_count=len(words),
        engine=engine_label,
        message=(
            "Text and QR payload extracted locally. Review and confirm below before analysing."
            if qr_payloads
            else "Text extracted locally. Review and confirm below before analysing."
        ),
        warnings=warnings,
    )
