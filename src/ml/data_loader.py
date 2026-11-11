"""Dataset loading, schema validation, and leakage-safe deduplication."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd


@dataclass(frozen=True)
class DatasetStats:
    raw_rows: int
    missing_or_invalid_rows: int
    duplicate_rows_removed: int
    clean_rows: int
    ham_count: int
    spam_count: int
    spam_ratio: float


def load_uci_sms_dataset(dataset_path: Path) -> tuple[pd.DataFrame, DatasetStats]:
    """Load and validate the tab-separated UCI SMS Spam Collection file.

    Deduplicates exact (label, text) pairs before any train/test split so
    repeated SMS templates cannot leak across evaluation splits.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(
            f"UCI dataset not found at {dataset_path}. Run 'python scripts/download_dataset.py' first."
        )

    rows: list[tuple[str, str]] = []
    invalid_rows = 0

    with dataset_path.open("r", encoding="utf-8", errors="replace") as fh:
        for raw_line in fh:
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                invalid_rows += 1
                continue
            parts = line.split("\t", maxsplit=1)
            if len(parts) != 2:
                invalid_rows += 1
                continue
            label = parts[0].strip().lower()
            text = parts[1].strip()
            if label not in {"ham", "spam"} or not text:
                invalid_rows += 1
                continue
            rows.append((label, text))

    raw_df = pd.DataFrame(rows, columns=["label", "text"])
    raw_count = len(raw_df)
    if raw_count == 0:
        raise ValueError(f"Dataset at {dataset_path} contained zero valid SMS rows.")

    dedup_df = raw_df.drop_duplicates(subset=["label", "text"]).reset_index(drop=True)
    # Remove cross-label collisions if any identical message appears in both classes
    text_counts = dedup_df["text"].value_counts()
    conflicting_texts = set(text_counts[text_counts > 1].index)
    if conflicting_texts:
        dedup_df = dedup_df[~dedup_df["text"].isin(conflicting_texts)].reset_index(drop=True)

    dedup_df["target"] = (dedup_df["label"] == "spam").astype(int)

    clean_count = len(dedup_df)
    duplicates_removed = raw_count - clean_count
    ham_count = int((dedup_df["target"] == 0).sum())
    spam_count = int((dedup_df["target"] == 1).sum())

    stats = DatasetStats(
        raw_rows=raw_count,
        missing_or_invalid_rows=invalid_rows,
        duplicate_rows_removed=duplicates_removed,
        clean_rows=clean_count,
        ham_count=ham_count,
        spam_count=spam_count,
        spam_ratio=round(spam_count / clean_count, 4) if clean_count else 0.0,
    )
    return dedup_df, stats


def dataset_stats_to_dict(stats: DatasetStats) -> Dict[str, int | float]:
    return {
        "raw_rows": stats.raw_rows,
        "missing_or_invalid_rows": stats.missing_or_invalid_rows,
        "duplicate_rows_removed": stats.duplicate_rows_removed,
        "clean_rows": stats.clean_rows,
        "ham_count": stats.ham_count,
        "spam_count": stats.spam_count,
        "spam_ratio": stats.spam_ratio,
    }
