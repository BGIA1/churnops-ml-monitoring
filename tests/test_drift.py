from __future__ import annotations

from typing import Any

import pandas as pd

from churnops.data import generate_dataset
from churnops.drift import (
    build_drift_report,
    categorical_total_variation,
    population_stability_index,
)


def test_drift_primitives_detect_distribution_changes() -> None:
    stable = pd.Series(range(1, 101))
    shifted = pd.Series(range(101, 201))
    assert population_stability_index(stable, stable) == 0
    assert population_stability_index(stable, shifted) > 0.25
    assert categorical_total_variation(pd.Series(["a", "a", "b"]), pd.Series(["a", "a", "b"])) == 0
    assert categorical_total_variation(pd.Series(["a", "a", "a"]), pd.Series(["b", "b", "b"])) == 1


def test_drift_report_flags_generated_drift(test_config: dict[str, Any]) -> None:
    reference = generate_dataset(500, seed=42, profile="training")
    drifted = generate_dataset(500, seed=43, profile="drifted")
    report = build_drift_report(reference, drifted, test_config)
    assert report["status"] == "alert"
    assert report["alerts"]
