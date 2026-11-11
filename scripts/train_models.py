"""CLI script to train TextVigil ML models and persist evaluation metrics."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.download_dataset import ensure_uci_dataset
from src.ml.model_training import train_and_evaluate


def main() -> int:
    ensure_uci_dataset()
    report = train_and_evaluate()
    ds = report["dataset"]
    print(
        f"[OK] Dataset: {ds['raw_rows']} raw -> {ds['clean_rows']} unique rows "
        f"(ham={ds['ham_count']}, spam={ds['spam_count']})"
    )
    print(f"[OK] Train/Test split: {ds['train_rows']} / {ds['test_rows']}")
    for key, m in report["models"].items():
        cm = m["confusion_matrix"]
        print(
            f"  - {m['display_name']}: Acc={m['accuracy']:.4f}, "
            f"Prec={m['precision']:.4f}, Rec={m['recall']:.4f}, "
            f"F1={m['f1_score']:.4f}, AUC={m['roc_auc']:.4f} "
            f"(TN={cm['tn']}, FP={cm['fp']}, FN={cm['fn']}, TP={cm['tp']})"
        )
    print(f"[OK] Selected default model: {report['selected_model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
