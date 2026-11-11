"""Unicode homoglyph, zero-width obfuscation, BiDi override, and URL trick auditor."""

from __future__ import annotations

import re
import unicodedata

from src.schemas import UnicodeAuditReport, UnicodeSpoofItem

ZERO_WIDTH_CHARS: dict[str, str] = {
    "\u200b": "Zero-Width Space (ZWSP)",
    "\u200c": "Zero-Width Non-Joiner (ZWNJ)",
    "\u200d": "Zero-Width Joiner (ZWJ)",
    "\u2060": "Word Joiner (WJ)",
    "\ufeff": "Zero-Width No-Break Space / BOM",
    "\u00ad": "Soft Hyphen",
    "\u034f": "Combining Grapheme Joiner",
    "\u180e": "Mongolian Vowel Separator",
}

BIDI_OVERRIDE_CHARS: set[str] = {
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\u200e",
    "\u200f",
}

# Common Cyrillic, Greek, and Latin lookalike confusables mapped to ASCII Latin equivalents
CONFUSABLE_TO_ASCII: dict[str, str] = {
    # Cyrillic lowercase
    "\u0430": "a",  # а
    "\u0432": "b",  # в (visual B/b confusable in caps contexts, kept conservative below if lowercase)
    "\u0435": "e",  # е
    "\u0451": "e",  # ё
    "\u0454": "e",  # є
    "\u0437": "3",  # з
    "\u0456": "i",  # і
    "\u0457": "i",  # ї
    "\u0458": "j",  # ј
    "\u043a": "k",  # к
    "\u043e": "o",  # о
    "\u0440": "p",  # р
    "\u0441": "c",  # с
    "\u0443": "y",  # у
    "\u0445": "x",  # х
    "\u0455": "s",  # ѕ
    "\u04bb": "h",  # һ
    "\u0501": "d",  # ԁ
    "\u051b": "q",  # ԛ
    "\u051d": "w",  # ԝ
    "\u04cf": "l",  # ӏ
    "\u043c": "m",  # м
    "\u0442": "t",  # т
    "\u043d": "h",  # н
    # Cyrillic uppercase
    "\u0410": "A",  # А
    "\u0412": "B",  # В
    "\u0415": "E",  # Е
    "\u0406": "I",  # І
    "\u0407": "I",  # Ї
    "\u0408": "J",  # Ј
    "\u041a": "K",  # К
    "\u041c": "M",  # М
    "\u041d": "H",  # Н
    "\u041e": "O",  # О
    "\u0420": "P",  # Р
    "\u0421": "C",  # С
    "\u0422": "T",  # Т
    "\u0425": "X",  # Х
    "\u0405": "S",  # Ѕ
    "\u0423": "Y",  # У
    # Greek lowercase
    "\u03b1": "a",  # α
    "\u03b5": "e",  # ε
    "\u03b9": "i",  # ι
    "\u03ba": "k",  # κ
    "\u03bd": "v",  # ν
    "\u03bf": "o",  # ο
    "\u03c1": "p",  # ρ
    "\u03c2": "c",  # ς
    "\u03c4": "t",  # τ
    "\u03c5": "u",  # υ
    "\u03c7": "x",  # χ
    # Greek uppercase
    "\u0391": "A",  # Α
    "\u0392": "B",  # Β
    "\u0395": "E",  # Ε
    "\u0396": "Z",  # Ζ
    "\u0397": "H",  # Η
    "\u0399": "I",  # Ι
    "\u039a": "K",  # Κ
    "\u039c": "M",  # Μ
    "\u039d": "N",  # Ν
    "\u039f": "O",  # Ο
    "\u03a1": "P",  # Ρ
    "\u03a4": "T",  # Τ
    "\u03a5": "Y",  # Υ
    "\u03a7": "X",  # Χ
    # Extended Latin lookalikes
    "\u0131": "i",  # dotless i ı
    "\u0261": "g",  # script g ɡ
    "\u1d04": "c",
    "\u1d0f": "o",
}

PROTECTED_BRAND_TERMS = (
    "sbi",
    "hdfc",
    "icici",
    "axis",
    "kotak",
    "pnb",
    "canara",
    "paytm",
    "phonepe",
    "gpay",
    "bhim",
    "npci",
    "indiapost",
    "bluedart",
    "dtdc",
    "uidai",
    "aadhaar",
    "epfo",
    "incometax",
    "rbi",
    "amazon",
    "flipkart",
    "apple",
    "google",
    "samplebank",
    "demobank",
    "sampleparcel",
    "yono",
    "otp",
    "kyc",
    "upi",
)

USERINFO_URL_RE = re.compile(
    r"(?i)(?:https?://[^\s<>\"']+@[^\s<>\"']+|\b[a-z0-9.-]+\.[a-z]{2,20}@[a-z0-9.-]+\.[a-z]{2,20}(?:/[^\s<>\"']*)?)"
)


def _is_indic_or_cjk(ch: str) -> bool:
    code = ord(ch)
    # Devanagari, Bengali, Gurmukhi, Gujarati, Oriya, Tamil, Telugu, Kannada, Malayalam
    return (0x0900 <= code <= 0x0DFF) or (0x4E00 <= code <= 0x9FFF)


def _canonicalize_token(token: str) -> tuple[str, int, int, int]:
    """Strip obfuscation from a single token and return (clean, zw_hits, homoglyph_hits, bidi_hits)."""
    nfkc = unicodedata.normalize("NFKC", token)
    out: list[str] = []
    zw_hits = 0
    homoglyph_hits = 0
    bidi_hits = 0

    chars = list(nfkc)
    for idx, ch in enumerate(chars):
        if ch in BIDI_OVERRIDE_CHARS:
            bidi_hits += 1
            continue
        if ch in ZERO_WIDTH_CHARS:
            prev_ch = chars[idx - 1] if idx > 0 else ""
            next_ch = chars[idx + 1] if idx + 1 < len(chars) else ""
            # ZWNJ/ZWJ inside pure Indic words (e.g. Malayalam chillu) is legitimate;
            # flag zero-width characters when adjacent to ASCII/Latin/URL symbols or when ZWSP/BOM/soft-hyphen
            is_indic_ligature = ch in {"\u200c", "\u200d"} and (
                _is_indic_or_cjk(prev_ch) or _is_indic_or_cjk(next_ch)
            )
            if not is_indic_ligature:
                zw_hits += 1
                continue
        mapped = CONFUSABLE_TO_ASCII.get(ch)
        if mapped is not None:
            homoglyph_hits += 1
            out.append(mapped)
        else:
            out.append(ch)
    return "".join(out), zw_hits, homoglyph_hits, bidi_hits


def deobfuscate_for_matching(raw_text: str) -> str:
    """Return a canonical ASCII-deobfuscated version of raw_text for rule & URL scanning."""
    if not raw_text:
        return ""
    # Process character stream preserving whitespace layout while cleaning confusables in suspicious tokens
    parts = re.split(r"(\s+)", raw_text)
    cleaned_parts: list[str] = []
    for part in parts:
        if not part or part.isspace():
            cleaned_parts.append(part)
            continue
        clean_tok, _, _, _ = _canonicalize_token(part)
        cleaned_parts.append(clean_tok)
    return "".join(cleaned_parts)


def audit_unicode_spoofing(raw_text: str) -> UnicodeAuditReport:
    """Inspect raw pre-normalized text for invisible obfuscation, homoglyphs, punycode, and @ tricks."""
    if not raw_text:
        return UnicodeAuditReport()

    total_zw = 0
    total_homoglyphs = 0
    total_bidi = 0
    findings: list[UnicodeSpoofItem] = []
    seen_issues: set[tuple[str, str]] = set()
    spoofed_brands: list[str] = []

    tokens = re.findall(r"\S+", raw_text)
    canonical_tokens: list[str] = []

    for tok in tokens:
        clean_tok, zw, hg, bidi = _canonicalize_token(tok)
        canonical_tokens.append(clean_tok)
        total_zw += zw
        total_homoglyphs += hg
        total_bidi += bidi

        lower_clean = clean_tok.lower()
        looks_url_or_latin = bool(
            re.search(r"[a-zA-Z0-9]", clean_tok)
            and ("." in clean_tok or "://" in clean_tok or len(clean_tok) >= 2)
        )

        if bidi > 0:
            key = ("bidi_override", clean_tok)
            if key not in seen_issues:
                seen_issues.add(key)
                findings.append(
                    UnicodeSpoofItem(
                        token=tok,
                        issue_type="bidi_override",
                        detail=f"Contains hidden directional override character(s) capable of disguising text/URL order near '{clean_tok}'.",
                        canonical_form=clean_tok,
                    )
                )

        if zw > 0:
            key = ("zero_width", clean_tok)
            if key not in seen_issues:
                seen_issues.add(key)
                findings.append(
                    UnicodeSpoofItem(
                        token=clean_tok,
                        issue_type="zero_width",
                        detail=f"Contains {zw} invisible zero-width character(s) inside '{clean_tok}' to slip past keyword filters.",
                        canonical_form=clean_tok,
                    )
                )

        # Avoid flagging legitimate non-Latin regional SMS sentences unless they mimic URLs/ASCII brands
        if hg > 0 and looks_url_or_latin:
            has_ascii_latin = any("a" <= c.lower() <= "z" for c in tok)
            matches_brand = any(brand in lower_clean for brand in PROTECTED_BRAND_TERMS)
            has_url_shape = (
                "://" in lower_clean
                or bool(re.search(r"\.[a-z]{2,12}\b", lower_clean))
            )
            if has_ascii_latin or matches_brand or has_url_shape:
                key = ("mixed_script_homoglyph", clean_tok)
                if key not in seen_issues:
                    seen_issues.add(key)
                    findings.append(
                        UnicodeSpoofItem(
                            token=tok,
                            issue_type="mixed_script_homoglyph",
                            detail=f"Uses {hg} non-Latin lookalike character(s) (Cyrillic/Greek) mimicking '{clean_tok}'.",
                            canonical_form=clean_tok,
                        )
                    )

        if "xn--" in lower_clean:
            key = ("punycode", lower_clean)
            if key not in seen_issues:
                seen_issues.add(key)
                findings.append(
                    UnicodeSpoofItem(
                        token=tok,
                        issue_type="punycode",
                        detail=f"Contains Punycode internationalized domain ('{clean_tok}'), frequently abused for lookalike phishing links.",
                        canonical_form=clean_tok,
                    )
                )

        if USERINFO_URL_RE.search(clean_tok):
            key = ("userinfo_trick", lower_clean)
            if key not in seen_issues:
                seen_issues.add(key)
                real_dest = clean_tok.split("@", 1)[-1].split("/", 1)[0]
                findings.append(
                    UnicodeSpoofItem(
                        token=tok,
                        issue_type="userinfo_trick",
                        detail=f"Uses '@' credential-redirect formatting — the real destination host is '{real_dest}', not the prefix shown before '@'.",
                        canonical_form=clean_tok,
                    )
                )

        if (zw > 0 or hg > 0 or bidi > 0) and (
            any(brand in lower_clean for brand in PROTECTED_BRAND_TERMS)
        ):
            for brand in PROTECTED_BRAND_TERMS:
                if brand in lower_clean and brand.upper() not in spoofed_brands:
                    spoofed_brands.append(brand.upper())

    has_obfuscation = len(findings) > 0
    canonical_joined = " ".join(canonical_tokens)
    raw_joined = " ".join(tokens)
    canonical_preview = canonical_joined if canonical_joined != raw_joined and has_obfuscation else None

    return UnicodeAuditReport(
        has_obfuscation=has_obfuscation,
        zero_width_count=total_zw,
        homoglyph_count=total_homoglyphs,
        bidi_control_count=total_bidi,
        spoofed_brands=spoofed_brands,
        canonical_preview=canonical_preview,
        findings=findings[:8],
    )
