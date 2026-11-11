"""Model evaluation metrics, threshold exploration curve, and feature importance."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline


def compute_threshold_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    thresholds: list[float] | None = None,
) -> list[dict[str, float | int]]:
    """Compute real precision, recall, F1, accuracy, FP, and FN across thresholds."""
    if thresholds is None:
        thresholds = [round(0.10 + 0.05 * i, 2) for i in range(17)]  # 0.10 to 0.90

    curve: list[dict[str, float | int]] = []
    for thr in thresholds:
        y_pred = (y_prob >= thr).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        curve.append(
            {
                "threshold": float(thr),
                "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
                "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
                "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
                "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            }
        )
    return curve


def extract_top_model_features(
    pipeline: Pipeline,
    model_key: str,
    top_n: int = 15,
) -> dict[str, list[dict[str, float | str]]]:
    """Extract highest-weight spam and ham features from a fitted TF-IDF pipeline."""
    vectorizer = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["clf"]
    feature_names = np.array(vectorizer.get_feature_names_out())

    if model_key == "logistic_regression":
        weights = clf.coef_[0]
    elif model_key == "multinomial_nb":
        weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    else:
        raise ValueError(f"Unsupported model key for feature inspection: {model_key}")

    top_spam_idx = np.argsort(weights)[::-1][:top_n]
    top_ham_idx = np.argsort(weights)[:top_n]

    spam_features = [
        {"feature": str(feature_names[idx]), "weight": round(float(weights[idx]), 4)}
        for idx in top_spam_idx
    ]
    ham_features = [
        {"feature": str(feature_names[idx]), "weight": round(float(weights[idx]), 4)}
        for idx in top_ham_idx
    ]
    return {"spam_indicators": spam_features, "ham_indicators": ham_features}


def evaluate_classifier(
    pipeline: Pipeline,
    model_key: str,
    display_name: str,
    X_test: Any,
    y_test: np.ndarray,
    default_threshold: float = 0.50,
) -> dict[str, Any]:
    """Evaluate a fitted pipeline strictly on held-out test data."""
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= default_threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
    report = classification_report(
        y_test,
        y_pred,
        target_names=["ham", "spam"],
        output_dict=True,
        zero_division=0,
    )

    return {
        "model_key": model_key,
        "display_name": display_name,
        "default_threshold": default_threshold,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "confusion_matrix": {
            "matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
            "labels": ["Legitimate (Ham)", "Spam"],
        },
        "classification_report": report,
        "threshold_curve": compute_threshold_curve(y_test, y_prob),
        "top_features": extract_top_model_features(pipeline, model_key, top_n=15),
        "vocabulary_size": int(len(pipeline.named_steps["tfidf"].vocabulary_)),
    }
