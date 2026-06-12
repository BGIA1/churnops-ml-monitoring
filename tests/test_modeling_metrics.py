from __future__ import annotations

from typing import Any

import numpy as np

from churnops.data import generate_dataset
from churnops.features import FEATURE_COLUMNS, LABEL_COLUMN
from churnops.metrics import classification_metrics
from churnops.modeling import build_pipeline, build_preprocessor, resolve_model_name


def test_preprocessor_and_pipeline_fit(test_config: dict[str, Any]) -> None:
    frame = generate_dataset(120, seed=22, profile="training")
    transformed = build_preprocessor().fit_transform(frame[FEATURE_COLUMNS])
    assert transformed.shape[0] == 120
    assert transformed.shape[1] > len(FEATURE_COLUMNS)

    pipeline = build_pipeline("logistic_regression", test_config)
    pipeline.fit(frame[FEATURE_COLUMNS], frame[LABEL_COLUMN])
    probabilities = pipeline.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
    assert np.all((probabilities >= 0) & (probabilities <= 1))


def test_metrics_include_business_errors_and_threshold() -> None:
    labels = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.8, 0.4, 0.9])
    metrics = classification_metrics(labels, probabilities, threshold=0.5)
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["false_positive"] == 1
    assert metrics["false_negative"] == 1
    assert metrics["threshold"] == 0.5
    assert metrics["roc_auc"] == 0.75


def test_cli_model_aliases_resolve_to_canonical_models() -> None:
    assert resolve_model_name("baseline") == "logistic_regression"
    assert resolve_model_name("candidate") == "random_forest"
