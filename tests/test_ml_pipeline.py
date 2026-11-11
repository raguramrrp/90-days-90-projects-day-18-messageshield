"""Tests for ML training, evaluation metrics, probability handling, and thresholds."""

from __future__ import annotations

from pathlib import Path

from src.config import DATASET_PATH, EVAL_PATH, MODEL_PATH
from src.ml.model_training import train_and_evaluate
from src.ml.prediction import load_evaluation_report, predict_message


def test_training_pipeline_produces_leakage_free_metrics(tmp_path: Path) -> None:
    model_out = tmp_path / "models.joblib"
    eval_out = tmp_path / "eval.json"

    report = train_and_evaluate(
        dataset_path=DATASET_PATH,
        model_output_path=model_out,
        eval_output_path=eval_out,
        random_state=42,
    )

    assert model_out.exists()
    assert eval_out.exists()
    assert report["dataset"]["train_rows"] + report["dataset"]["test_rows"] == report["dataset"]["clean_rows"]
    assert "logistic_regression" in report["models"]
    assert "multinomial_nb" in report["models"]

    for model_key in ("logistic_regression", "multinomial_nb"):
        metrics = report["models"][model_key]
        assert 0.90 <= metrics["accuracy"] <= 1.0
        assert 0.85 <= metrics["precision"] <= 1.0
        assert 0.75 <= metrics["recall"] <= 1.0
        assert len(metrics["threshold_curve"]) == 17
        assert len(metrics["top_features"]["spam_indicators"]) == 15
        cm = metrics["confusion_matrix"]
        assert cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] == report["dataset"]["test_rows"]


def test_persisted_model_inference_and_threshold_sensitivity() -> None:
    assert MODEL_PATH.exists()
    assert EVAL_PATH.exists()
    report = load_evaluation_report(EVAL_PATH)
    assert report["selected_model"] in {"logistic_regression", "multinomial_nb"}

    spam_msg = "FREE entry into weekly prize draw! Text WIN to 80085 now to claim your £1000 reward!"
    ham_msg = "Hey, are we still meeting for lunch near the library at 1 PM today?"

    pred_spam = predict_message(spam_msg, model_name="logistic_regression", threshold=0.50)
    pred_ham = predict_message(ham_msg, model_name="logistic_regression", threshold=0.50)

    assert pred_spam.ml_classification == "Spam / Suspicious"
    assert pred_spam.raw_spam_score > 0.70
    assert pred_spam.is_calibrated is False
    assert len(pred_spam.top_contributions) > 0

    assert pred_ham.ml_classification == "Legitimate (Ham)"
    assert pred_ham.raw_spam_score < 0.30

    # Threshold boundary test: shifting threshold changes classification consistently
    borderline_score = pred_spam.raw_spam_score
    low_thr = predict_message(spam_msg, model_name="logistic_regression", threshold=max(0.10, borderline_score - 0.15))
    high_thr = predict_message(spam_msg, model_name="logistic_regression", threshold=min(0.95, borderline_score + 0.05))
    if borderline_score < 0.95:
        assert low_thr.ml_classification == "Spam / Suspicious"
        assert high_thr.ml_classification == "Legitimate (Ham)"
