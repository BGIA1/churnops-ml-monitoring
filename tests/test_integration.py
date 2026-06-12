from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from churnops.config import configured_path
from churnops.data import generate_all
from churnops.service import (
    batch_score,
    controlled_retrain,
    get_registry,
    monitor_drift,
    monitor_performance,
    promote_candidate,
    train_model,
)


@pytest.mark.integration
def test_training_promotion_scoring_monitoring_and_retraining(
    test_config: dict[str, Any],
) -> None:
    generate_all(test_config)
    baseline = train_model(test_config, model_name="logistic_regression")
    promotion = promote_candidate(test_config, baseline["version"])
    assert promotion["promoted"]
    assert get_registry(test_config).champion_exists()

    scoring = batch_score(test_config)
    scored = pd.read_csv(scoring["output"])
    assert {"prediction", "churn_probability"}.issubset(scored.columns)
    assert len(scored) == test_config["data"]["batch_rows"]

    drift = monitor_drift(test_config)
    performance = monitor_performance(test_config)
    retraining = controlled_retrain(test_config)
    assert drift["status"] in {"ok", "alert"}
    assert performance["current_metrics"]["roc_auc"] is not None
    assert "promoted" in retraining["promotion"]
    assert configured_path(test_config, "reports_dir").joinpath("retraining-report.json").exists()


@pytest.mark.integration
def test_repeated_promotion_of_rejected_candidate_is_controlled(
    test_config: dict[str, Any],
) -> None:
    generate_all(test_config)
    baseline = train_model(test_config, model_name="logistic_regression")
    assert promote_candidate(test_config, baseline["version"])["promoted"]

    weak_candidate = train_model(test_config, model_name="dummy")
    first = promote_candidate(test_config, weak_candidate["version"])
    second = promote_candidate(test_config, weak_candidate["version"])

    assert not first["promoted"]
    assert first["status"] == "rejected"
    assert not second["promoted"]
    assert second["status"] == "already_rejected"
    assert second["already_rejected"]
