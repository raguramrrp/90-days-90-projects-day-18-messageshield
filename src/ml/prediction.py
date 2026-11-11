"""Inference engine with per-message TF-IDF feature contribution explanations."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from src.config import EVAL_PATH, MODEL_PATH
from src.schemas import MLPredictionInfo, TokenContribution

MODEL_DISPLAY_NAMES = {
    "logistic_regression": "Logistic Regression (TF-IDF)",
    "multinomial_nb": "Multinomial Naive Bayes (TF-IDF)",
}

CALIBRATION_NOTE = (
    "Score reflects uncalibrated classifier confidence on UCI SMS patterns; "
    "do not interpret as a calibrated real-world fraud probability."
)


class ModelArtifactNotFoundError(RuntimeError):
    """Raised when saved ML artifacts have not been trained yet."""


@lru_cache(maxsize=2)
def _load_bundle(model_path_str: str) -> dict[str, Any]:
    path = Path(model_path_str)
    if not path.exists():
        raise ModelArtifactNotFoundError(
            f"Trained model artifact missing at {path}. Run 'python scripts/train_models.py'."
        )
    return joblib.load(path)


@lru_cache(maxsize=2)
def load_evaluation_report(eval_path: Path = EVAL_PATH) -> dict[str, Any]:
    if not eval_path.exists():
        raise ModelArtifactNotFoundError(
            f"Evaluation report missing at {eval_path}. Run 'python scripts/train_models.py'."
        )
    return json.loads(eval_path.read_text(encoding="utf-8"))


def clear_model_cache() -> None:
    _load_bundle.cache_clear()
    load_evaluation_report.cache_clear()


def is_model_ready(model_path: Path = MODEL_PATH) -> bool:
    return model_path.exists()


def predict_message(
    text: str,
    model_name: str | None = None,
    threshold: float = 0.50,
    model_path: Path = MODEL_PATH,
    top_k_tokens: int = 8,
) -> MLPredictionInfo:
    """Run binary spam inference and extract per-message feature contributions."""
    bundle = _load_bundle(str(model_path))
    models = bundle["models"]
    chosen_key = model_name or bundle.get("selected_model", "logistic_regression")
    if chosen_key not in models:
        raise ValueError(f"Unknown model '{chosen_key}'. Available: {list(models.keys())}")

    pipeline = models[chosen_key]
    raw_spam_prob = float(pipeline.predict_proba([text])[0][1])
    ml_label = "Spam / Suspicious" if raw_spam_prob >= threshold else "Legitimate (Ham)"

    # Compute genuine per-message token contributions from TF-IDF vector * model weights
    vectorizer = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["clf"]
    vec = vectorizer.transform([text])
    feature_names = vectorizer.get_feature_names_out()

    if chosen_key == "logistic_regression":
        weights = clf.coef_[0]
    else:
        weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]

    contributions: list[TokenContribution] = []
    if vec.nnz > 0:
        indices = vec.indices
        values = vec.data
        scored = []
        for idx, tfidf_val in zip(indices, values):
            token = str(feature_names[idx])
            contrib = float(tfidf_val * weights[idx])
            if abs(contrib) > 1e-4:
                scored.append((token, contrib))
        # Sort by largest absolute contribution so both spam & ham evidence show clearly
        scored.sort(key=lambda item: abs(item[1]), reverse=True)
        for token, contrib in scored[:top_k_tokens]:
            contributions.append(
                TokenContribution(
                    token=token,
                    weight=round(contrib, 4),
                    direction="spam" if contrib > 0 else "ham",
                )
            )

    return MLPredictionInfo(
        model_name=chosen_key,
        model_display_name=MODEL_DISPLAY_NAMES.get(chosen_key, chosen_key),
        ml_classification=ml_label,
        raw_spam_score=round(raw_spam_prob, 4),
        threshold_used=round(float(threshold), 2),
        is_calibrated=False,
        calibration_note=CALIBRATION_NOTE,
        top_contributions=contributions,
    )
