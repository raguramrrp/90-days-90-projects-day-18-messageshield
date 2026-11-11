"""Generate bundled demonstration assets: batch sample CSV and realistic SMS/QR screenshots."""

from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCREENSHOT_DIR = DATA_DIR / "sample_screenshots"
SAMPLE_CSV_PATH = DATA_DIR / "sample_batch_messages.csv"

SAMPLE_BATCH_ROWS = [
    (
        "1",
        "JD-CLINIC-S",
        "Reminder: Your dental consultation at Sample Care Clinic is scheduled for tomorrow at 10:30 AM. Reply YES to confirm.",
        "Legitimate appointment",
    ),
    (
        "2",
        "AD-DMOBNK-T",
        "A/c XX0000 debited for INR 1,450.00 on 11-11-26 at DemoMart via Ref No. 000000000000. If not done by you, call 1800-000-0000 or block card in official SampleBank app. Never share OTP.",
        "Legitimate bank alert",
    ),
    (
        "3",
        "VK-DMOBSK-P",
        "DemoMart Weekend Sale: Flat 20% off on fresh groceries above Rs.999. Use code DEMO20 in the DemoMart app before Sunday. T&C apply. Reply STOP to opt out.",
        "Promotional offer",
    ),
    (
        "4",
        "VK-DMOKYC",
        "Dear customer, your SampleBank account KYC has expired today. Your account will be blocked within 2 hours. Update KYC immediately at http://samplebank-kyc.xyz/verify",
        "Fake KYC phishing",
    ),
    (
        "5",
        "+91 00000 00003",
        "Sample Parcel Service: Your parcel DEMO000001 is held at sorting hub due to incomplete address. Pay Rs.25 redelivery fee within 12 hrs at http://parcel-redelivery-demo.xyz/pay",
        "Fake courier fee + mobile spoof",
    ),
    (
        "6",
        "HR-TASK",
        "Part-time Work From Home! Earn Rs.3,500 daily by rating sample videos online. Pay Rs.499 registration fee to activate account. Message +91-0000000001",
        "Job registration scam",
    ),
    (
        "7",
        "DMOCBK",
        "Congratulations! You received Rs.4,999 UPI cashback reward. Approve the pending UPI collect request and enter your UPI PIN to claim before tonight.",
        "UPI collect scam",
    ),
    (
        "8",
        "JX-DISCOM-S",
        "SamplePower Electricity: Bill for Consumer No. 00000000 for Oct 2026 is Rs.1,120. Due date 25-11-2026. Pay via official portal or BBPS app.",
        "Legitimate utility notice",
    ),
    (
        "9",
        "+91 00000 00002",
        "URGENT: Your electricity power will be disconnected tonight at 9:30 PM because previous month bill was not updated. Call electricity officer immediately on +91 00000 00002.",
        "Electricity disconnection + mobile spoof",
    ),
    (
        "10",
        "DMOWIN",
        "Lucky Winner! You won a flagship smartphone in festive draw. Claim your reward now at http://198.51.100.22/claim?token=demo99",
        "Fake reward + IP link",
    ),
    (
        "11",
        "+91 00000 00001",
        "Congrats! Claim your Rs.4,999 festive cashback right now using your verified payout link: upi://pay?pa=demo-cashback@exampleupi&pn=Demo%20Reward&am=4999&cu=INR",
        "UPI deep-link payment bait",
    ),
    (
        "12",
        "JM-DMOKYC-P",
        "Dear customer, your SampleBank account KYC has expired today. Your account will be blocked within 2 hours. Update KYC immediately at http://samplebank-fresh.top/verify",
        "Campaign rotated domain + -P misuse",
    ),
    (
        "13",
        "JX-DMOLNK-P",
        "Urgent: Re-verify your S\u200ba\u200bm\u200bp\u200bl\u200beBank profile with O\u200bT\u200bP before midnight at https://samplebank.example@demo-redirect.xyz/auth",
        "Zero-width + @ userinfo redirect",
    ),
    (
        "14",
        "+91 00000 00002",
        "SampleBank Alert: Unusual login from unknown device. Secure your profile now at https://\u0455amplebank-secure.xyz/login or xn--smplbnk-k4a.top before block.",
        "Cyrillic homoglyph + punycode + mobile spoof",
    ),
    (
        "15",
        "+91 00000 00005",
        "Traffic E-Challan Notice (Demo): Vehicle fine Rs.2,000 pending. Download Demo_Challan.apk from http://demo-challan-pay.icu/app or install a remote screen-share app to settle now.",
        "Fake E-Challan .apk + remote screen-share trap",
    ),
]


def _encode_qr_v5_l(text: str) -> list[list[int]]:
    """Minimal self-contained ISO 18004 QR Code Version 5-L (37x37, up to 106 UTF-8 bytes)."""
    payload = text.encode("utf-8")
    if len(payload) > 106:
        raise ValueError("Payload exceeds Version 5-L 106-byte limit")

    # GF(256) with primitive polynomial 0x11D
    exp = [0] * 512
    log = [0] * 256
    x = 1
    for i in range(255):
        exp[i] = x
        log[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D
    for i in range(255, 512):
        exp[i] = exp[i - 255]

    def gf_mul(a: int, b: int) -> int:
        return 0 if (a == 0 or b == 0) else exp[log[a] + log[b]]

    # Build generator polynomial of degree 26 for Version 5-L (108 data + 26 EC = 134 codewords)
    ec_len = 26
    gen = [1]
    for i in range(ec_len):
        nxt = [0] * (len(gen) + 1)
        root = exp[i]
        for j, g in enumerate(gen):
            nxt[j] ^= g
            nxt[j + 1] ^= gf_mul(g, root)
        gen = nxt

    # Encode Byte mode bitstream (0100 + 8-bit length + bytes + terminator + pad)
    bits: list[int] = []

    def push_bits(val: int, width: int) -> None:
        for shift in range(width - 1, -1, -1):
            bits.append((val >> shift) & 1)

    push_bits(0b0100, 4)
    push_bits(len(payload), 8)
    for b in payload:
        push_bits(b, 8)

    data_cap_bits = 108 * 8
    term_len = min(4, data_cap_bits - len(bits))
    push_bits(0, term_len)
    while len(bits) % 8 != 0:
        bits.append(0)

    data_bytes = [
        int("".join(str(b) for b in bits[i : i + 8]), 2)
        for i in range(0, len(bits), 8)
    ]
    pad_cycle = [0xEC, 0x11]
    idx = 0
    while len(data_bytes) < 108:
        data_bytes.append(pad_cycle[idx % 2])
        idx += 1

    # Polynomial division for 26 Reed-Solomon EC codewords
    msg_buf = data_bytes + [0] * ec_len
    for i in range(len(data_bytes)):
        coef = msg_buf[i]
        if coef != 0:
            for j in range(1, len(gen)):
                msg_buf[i + j] ^= gf_mul(gen[j], coef)
    codewords = data_bytes + msg_buf[len(data_bytes) :]

    # Version 5 remaining bits = 7 zero bits
    stream_bits: list[int] = []
    for cw in codewords:
        for shift in range(7, -1, -1):
            stream_bits.append((cw >> shift) & 1)
    stream_bits.extend([0] * 7)

    size = 37
    grid = [[-1] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]

    def set_mod(r: int, c: int, val: int, res: bool = True) -> None:
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = val
            if res:
                reserved[r][c] = True

    def place_finder(top: int, left: int) -> None:
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                r, c = top + dr, left + dc
                if not (0 <= r < size and 0 <= c < size):
                    continue
                if dr in (-1, 7) or dc in (-1, 7):
                    set_mod(r, c, 0)
                elif dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4):
                    set_mod(r, c, 1)
                else:
                    set_mod(r, c, 0)

    def place_alignment(center_r: int, center_c: int) -> None:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                val = 1 if (abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0)) else 0
                set_mod(center_r + dr, center_c + dc, val)

    place_finder(0, 0)
    place_finder(0, size - 7)
    place_finder(size - 7, 0)
    place_alignment(30, 30)

    for i in range(8, size - 8):
        set_mod(6, i, 1 if i % 2 == 0 else 0)
        set_mod(i, 6, 1 if i % 2 == 0 else 0)

    # Dark module (4*V + 9, 8)
    set_mod(4 * 5 + 9, 8, 1)

    # Reserve format info areas around finders
    for i in range(9):
        if i != 6:
            reserved[8][i] = True
            reserved[i][8] = True
    for i in range(8):
        reserved[8][size - 1 - i] = True
        reserved[size - 1 - i][8] = True

    # Place data bits bottom-right zigzag skipping column 6
    bit_idx = 0
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        row_range = range(size - 1, -1, -1) if upward else range(size)
        for r in row_range:
            for dc in (0, -1):
                c = col + dc
                if not reserved[r][c]:
                    b = stream_bits[bit_idx] if bit_idx < len(stream_bits) else 0
                    bit_idx += 1
                    # Apply Mask Pattern 0: (r + c) % 2 == 0
                    if (r + c) % 2 == 0:
                        b ^= 1
                    grid[r][c] = b
        upward = not upward
        col -= 2

    # Format info for EC Level L (01) + Mask 0 (000) -> BCH + 0x5412 mask = 0x77C4 (111011111000100)
    fmt = 0x77C4
    fmt_bits = [(fmt >> i) & 1 for i in range(14, -1, -1)]
    # Top-left around finder
    coords_a = [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8), (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)]
    coords_b = [(size - 1 - i, 8) for i in range(7)] + [(8, size - 8 + j) for j in range(8)]
    for idx_f, (r, c) in enumerate(coords_a):
        grid[r][c] = fmt_bits[idx_f]
    for idx_f, (r, c) in enumerate(coords_b):
        grid[r][c] = fmt_bits[idx_f]

    return grid


def _draw_sms_screenshot(
    output_path: Path,
    sender: str,
    lines: list[str],
    time_label: str = "10:42 AM",
) -> None:
    width, height = 720, 440
    img = Image.new("RGB", (width, height), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("arial.ttf", 28)
        font_body = ImageFont.truetype("arial.ttf", 25)
        font_meta = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    draw.rectangle([(0, 0), (width, 84)], fill=(15, 41, 66))
    draw.text((32, 26), f"Messages  |  {sender}", fill=(255, 255, 255), font=font_header)

    draw.rounded_rectangle(
        [(28, 114), (width - 28, height - 48)],
        radius=20,
        fill=(255, 255, 255),
        outline=(210, 214, 220),
        width=2,
    )
    y = 140
    for line in lines:
        draw.text((52, y), line, fill=(20, 24, 31), font=font_body)
        y += 38

    draw.text((52, height - 86), f"SMS  •  {time_label}", fill=(107, 114, 128), font=font_meta)
    img.save(output_path, format="PNG")


def _draw_qr_upi_scam_screenshot(
    output_path: Path,
    upi_payload: str,
    sender_label: str = "+91 00000 00001",
    headline_1: str = "Congratulations! You unlocked Rs.4,999",
    headline_2: str = "festive cashback reward.",
    prompt_line: str = "Scan this QR & enter UPI PIN to receive:",
    footer_line: str = "Demo Cashback QR  •  Sample Showcase",
) -> None:
    """Create a realistic WhatsApp/SMS QR payment lure card verified by cv2.QRCodeDetector."""
    width, height = 720, 620
    img = Image.new("RGB", (width, height), color=(248, 249, 250))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("arial.ttf", 26)
        font_body = ImageFont.truetype("arial.ttf", 24)
        font_meta = ImageFont.truetype("arial.ttf", 19)
    except OSError:
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_meta = ImageFont.load_default()

    draw.rectangle([(0, 0), (width, 82)], fill=(24, 24, 27))
    draw.text((32, 25), f"Messages  |  {sender_label}", fill=(255, 255, 255), font=font_header)

    draw.rounded_rectangle(
        [(28, 108), (width - 28, height - 32)],
        radius=20,
        fill=(255, 255, 255),
        outline=(212, 212, 216),
        width=2,
    )
    draw.text((52, 134), headline_1, fill=(20, 24, 31), font=font_body)
    draw.text((52, 168), headline_2, fill=(20, 24, 31), font=font_body)
    draw.text((52, 206), prompt_line, fill=(63, 63, 70), font=font_meta)

    matrix = _encode_qr_v5_l(upi_payload)
    mod_size = 7
    quiet = 4 * mod_size
    qr_dim = len(matrix) * mod_size + 2 * quiet
    qr_left = (width - qr_dim) // 2
    qr_top = 248

    draw.rectangle(
        [(qr_left, qr_top), (qr_left + qr_dim, qr_top + qr_dim)],
        fill=(255, 255, 255),
        outline=(228, 228, 231),
        width=1,
    )
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val == 1:
                x0 = qr_left + quiet + c * mod_size
                y0 = qr_top + quiet + r * mod_size
                draw.rectangle([(x0, y0), (x0 + mod_size - 1, y0 + mod_size - 1)], fill=(0, 0, 0))

    draw.text((52, height - 68), footer_line, fill=(107, 114, 128), font=font_meta)
    img.save(output_path, format="PNG")

    # Verify with OpenCV right away so demo & tests are 100% deterministic
    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread(str(output_path)))
    if decoded.strip() != upi_payload:
        raise RuntimeError(f"Generated QR failed verification: got {decoded!r}, expected {upi_payload!r}")


def generate_assets() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    with SAMPLE_CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "sender", "message", "expected_note"])
        writer.writerows(SAMPLE_BATCH_ROWS)

    _draw_sms_screenshot(
        SCREENSHOT_DIR / "sample_kyc_scam.png",
        sender="VK-DMOKYC",
        lines=[
            "Dear customer, your SampleBank KYC has",
            "expired today. Account will be blocked",
            "within 2 hours. Update KYC immediately at",
            "http://samplebank-kyc.xyz/verify",
        ],
    )
    _draw_sms_screenshot(
        SCREENSHOT_DIR / "sample_legit_bank_alert.png",
        sender="AD-DMOBNK-T",
        lines=[
            "A/c XX0000 debited for INR 1,450.00 on",
            "11-11-26 at DemoMart via Ref 000000000000.",
            "If not done by you, call 1800-000-0000.",
            "Never share OTP with anyone.",
        ],
    )
    _draw_qr_upi_scam_screenshot(
        SCREENSHOT_DIR / "sample_qr_upi_scam.png",
        upi_payload="upi://pay?pa=demo-cashback@exampleupi&pn=Demo%20Cashback&am=4999&cu=INR&tn=Demo%20Claim",
        sender_label="+91 00000 00001",
    )
    _draw_qr_upi_scam_screenshot(
        SCREENSHOT_DIR / "sample_qr_mandate_scam.png",
        upi_payload="upi://mandate?pa=demo-refund@testupi&pn=Demo%20Parcel&am=2400&cu=INR&tn=Demo",
        sender_label="+91 00000 00002",
        headline_1="Sample Parcel: Your parcel refund of",
        headline_2="Rs.2,400 is ready for instant payout.",
        prompt_line="Scan QR & enter UPI PIN to confirm mandate:",
        footer_line="Demo Refund Mandate  •  Sample Showcase",
    )

    blank = Image.new("RGB", (320, 180), color=(240, 240, 240))
    blank.save(SCREENSHOT_DIR / "blank_unreadable.png", format="PNG")
    print(f"[OK] Generated {SAMPLE_CSV_PATH} and sample screenshots (incl. verified QR scam) in {SCREENSHOT_DIR}")


if __name__ == "__main__":
    generate_assets()
