"""Safe CSV upload validation, column inspection, batch scan, and sanitized CSV export."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from src.config import MAX_CSV_MB, MAX_CSV_ROWS, MAX_MESSAGE_CHARS
from src.core.explanation import analyze_message
from src.schemas import BatchAnalyzeResponse, BatchInspectResponse, BatchRowResult

SUGGESTED_COLUMN_NAMES = ("message", "text", "sms", "body", "content", "v2")
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _decode_csv_bytes(raw_bytes: bytes, filename: str) -> str:
    if Path(filename).suffix.lower() != ".csv":
        raise ValueError("Only .csv files are supported for batch analysis.")
    if not raw_bytes:
        raise ValueError("Uploaded CSV file is empty.")
    max_bytes = MAX_CSV_MB * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise ValueError(f"CSV file exceeds the {MAX_CSV_MB} MB limit.")

    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode CSV file as UTF-8 or standard Windows text.")


def _parse_csv_rows(text_data: str) -> tuple[list[str], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(text_data))
    if not reader.fieldnames:
        raise ValueError("CSV file has no header row.")
    columns = [col.strip() for col in reader.fieldnames if col is not None and col.strip()]
    if not columns:
        raise ValueError("CSV header row contains no valid column names.")

    rows: list[dict[str, str]] = []
    for idx, row in enumerate(reader):
        if idx >= MAX_CSV_ROWS:
            raise ValueError(f"CSV exceeds maximum allowed {MAX_CSV_ROWS} rows per batch.")
        cleaned = {
            (k.strip() if k else ""): (v or "")
            for k, v in row.items()
            if k is not None and k.strip()
        }
        rows.append(cleaned)

    if not rows:
        raise ValueError("CSV file contains headers but zero data rows.")
    return columns, rows


def inspect_csv_bytes(raw_bytes: bytes, filename: str = "messages.csv") -> BatchInspectResponse:
    text_data = _decode_csv_bytes(raw_bytes, filename)
    columns, rows = _parse_csv_rows(text_data)

    lower_map = {c.lower(): c for c in columns}
    suggested = columns[0]
    for candidate in SUGGESTED_COLUMN_NAMES:
        if candidate in lower_map:
            suggested = lower_map[candidate]
            break

    return BatchInspectResponse(
        filename=Path(filename).name,
        row_count=len(rows),
        columns=columns,
        suggested_column=suggested,
        preview_rows=rows[:3],
    )


def analyze_csv_bytes(
    raw_bytes: bytes,
    filename: str,
    text_column: str,
    model_name: str | None = None,
    threshold: float = 0.50,
    url_reputation_mode: str = "local_only",
) -> BatchAnalyzeResponse:
    text_data = _decode_csv_bytes(raw_bytes, filename)
    columns, rows = _parse_csv_rows(text_data)

    if text_column not in columns:
        raise ValueError(f"Selected column '{text_column}' does not exist in CSV headers: {columns}")

    lower_col_map = {c.lower(): c for c in columns}
    sender_column: str | None = None
    for candidate in ("sender", "sender_id", "from"):
        found_col = lower_col_map.get(candidate)
        if found_col and found_col != text_column:
            sender_column = found_col
            break

    results: list[BatchRowResult] = []
    skipped = 0
    summary_counts: dict[str, int] = {
        "Safe / Normal": 0,
        "Promotional": 0,
        "Suspicious / Flagged": 0,
        "Needs Review": 0,
    }

    for idx, row in enumerate(rows, start=1):
        msg = (row.get(text_column) or "").strip()
        if not msg:
            skipped += 1
            continue
        truncated = msg[:MAX_MESSAGE_CHARS]
        row_sender = (row.get(sender_column) or "").strip() or None if sender_column else None
        res = analyze_message(
            raw_message=truncated,
            model_name=model_name,
            threshold=threshold,
            url_reputation_mode=url_reputation_mode,
            sender_id=row_sender,
        )
        if res.threat_category == "Safe / Normal":
            summary_counts["Safe / Normal"] += 1
        elif res.threat_category == "Promotional":
            summary_counts["Promotional"] += 1
        elif res.threat_category == "Needs Review":
            summary_counts["Needs Review"] += 1
        else:
            summary_counts["Suspicious / Flagged"] += 1

        results.append(
            BatchRowResult(
                row_index=idx,
                message=res.message,
                classification=res.classification,
                threat_category=res.threat_category,
                risk_level=res.risk_level,
                raw_spam_score=res.ml_prediction.raw_spam_score,
                url_count=res.url_analysis.count,
                top_intent=res.detected_intents[0].intent if res.detected_intents else None,
                summary=res.summary,
            )
        )

    return BatchAnalyzeResponse(
        filename=Path(filename).name,
        text_column=text_column,
        total_rows=len(rows),
        processed_rows=len(results),
        skipped_empty_rows=skipped,
        summary_counts=summary_counts,
        results=results,
    )


def _sanitize_csv_cell(value: str) -> str:
    """Prevent spreadsheet formula injection when exporting user-supplied text."""
    if value and value[0] in FORMULA_PREFIXES:
        return "'" + value
    return value


def export_batch_results_csv(results: list[BatchRowResult]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "row_index",
            "message",
            "classification",
            "threat_category",
            "risk_level",
            "ml_spam_score",
            "url_count",
            "top_intent",
            "summary",
        ]
    )
    for item in results:
        writer.writerow(
            [
                item.row_index,
                _sanitize_csv_cell(item.message),
                item.classification,
                item.threat_category,
                item.risk_level,
                f"{item.raw_spam_score:.4f}",
                item.url_count,
                item.top_intent or "",
                _sanitize_csv_cell(item.summary),
            ]
        )
    return output.getvalue()
