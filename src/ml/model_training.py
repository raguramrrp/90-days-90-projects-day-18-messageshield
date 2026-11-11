"""Reproducible NLP model training and artifact persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from src.config import DATASET_PATH, EVAL_PATH, MODEL_PATH
from src.ml.data_loader import dataset_stats_to_dict, load_uci_sms_dataset
from src.ml.model_evaluation import evaluate_classifier
from src.ml.preprocessing import preprocess_for_model

RANDOM_SEED = 42
TOKEN_PATTERN = r"(?u)\b\w+\b|[!?₹$£]"


def _build_tfidf() -> TfidfVectorizer:
    return TfidfVectorizer(
        preprocessor=preprocess_for_model,
        token_pattern=TOKEN_PATTERN,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.98,
        max_features=15000,
        sublinear_tf=True,
    )


def train_and_evaluate(
    dataset_path: Path = DATASET_PATH,
    model_output_path: Path = MODEL_PATH,
    eval_output_path: Path = EVAL_PATH,
    random_state: int = RANDOM_SEED,
) -> dict[str, Any]:
    """Train Logistic Regression and Multinomial Naive Bayes without data leakage."""
    df, stats = load_uci_sms_dataset(dataset_path)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"].values,
        df["target"].values,
        test_size=0.20,
        stratify=df["target"].values,
        random_state=random_state,
    )

    pipelines = {
        "logistic_regression": (
            "Logistic Regression (TF-IDF)",
            Pipeline(
                [
                    ("tfidf", _build_tfidf()),
                    (
                        "clf",
                        LogisticRegression(
                            max_iter=1000,
                            C=4.0,
                            solver="lbfgs",
                            random_state=random_state,
                        ),
                    ),
                ]
            ),
        ),
        "multinomial_nb": (
            "Multinomial Naive Bayes (TF-IDF)",
            Pipeline(
                [
                    ("tfidf", _build_tfidf()),
                    ("clf", MultinomialNB(alpha=0.25)),
                ]
            ),
        ),
    }

    trained_models: dict[str, Pipeline] = {}
    evaluations: dict[str, dict[str, Any]] = {}

    for model_key, (display_name, pipeline) in pipelines.items():
        # Fit strictly on training split so test vocabulary and IDF weights never leak
        pipeline.fit(X_train, y_train)
        trained_models[model_key] = pipeline
        evaluations[model_key] = evaluate_classifier(
            pipeline=pipeline,
            model_key=model_key,
            display_name=display_name,
            X_test=X_test,
            y_test=y_test,
            default_threshold=0.50,
        )

    # Select recommended model by highest F1-score, breaking ties with precision (low FP)
    selected_model = max(
        evaluations.keys(),
        key=lambda k: (
            evaluations[k]["f1_score"],
            evaluations[k]["precision"],
            evaluations[k]["roc_auc"],
        ),
    )

    trained_at = datetime.now(timezone.utc).isoformat()
    report: dict[str, Any] = {
        "dataset": {
            "name": "UCI SMS Spam Collection v.1",
            "source_url": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
            "license": "CC BY 4.0 / Public Research Corpus (Almeida et al., 2011)",
            **dataset_stats_to_dict(stats),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "train_spam_count": int(y_train.sum()),
            "test_spam_count": int(y_test.sum()),
            "split_strategy": f"Stratified 80/20 split after exact deduplication (seed={random_state})",
        },
        "trained_at": trained_at,
        "random_seed": random_state,
        "selected_model": selected_model,
        "selection_rationale": (
            f"{evaluations[selected_model]['display_name']} selected based on held-out "
            f"F1-score ({evaluations[selected_model]['f1_score']:.4f}) and precision "
            f"({evaluations[selected_model]['precision']:.4f}) to minimize false positives."
        ),
        "calibration_note": (
            "Raw TF-IDF classifier scores reflect statistical similarity to the 2011 UCI SMS corpus "
            "and are not calibrated real-world fraud probabilities."
        ),
        "models": evaluations,
    }

    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    eval_output_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_bundle = {
        "models": trained_models,
        "selected_model": selected_model,
        "trained_at": trained_at,
        "random_state": random_state,
    }
    joblib.dump(artifact_bundle, model_output_path)
    eval_output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    return report
