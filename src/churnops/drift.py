"""Feature and prediction drift calculations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from churnops.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    *,
    bins: int = 10,
) -> float:
    reference_values = reference.astype(float).to_numpy()
    current_values = current.astype(float).to_numpy()
    edges = np.unique(np.quantile(reference_values, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    reference_counts, _ = np.histogram(reference_values, bins=edges)
    current_counts, _ = np.histogram(current_values, bins=edges)
    reference_ratio = np.clip(reference_counts / max(reference_counts.sum(), 1), 1e-6, None)
    current_ratio = np.clip(current_counts / max(current_counts.sum(), 1), 1e-6, None)
    psi_values = (current_ratio - reference_ratio) * np.log(current_ratio / reference_ratio)
    return float(np.sum(psi_values))


def categorical_total_variation(reference: pd.Series, current: pd.Series) -> float:
    categories = sorted(set(reference.astype(str)) | set(current.astype(str)))
    reference_dist = (
        reference.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0)
    )
    current_dist = (
        current.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0)
    )
    return float(0.5 * np.abs(reference_dist - current_dist).sum())


def build_drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    config: dict[str, Any],
    *,
    reference_probabilities: np.ndarray | None = None,
    current_probabilities: np.ndarray | None = None,
) -> dict[str, Any]:
    monitoring = config["monitoring"]
    numeric: dict[str, Any] = {}
    categorical: dict[str, Any] = {}
    alerts: list[str] = []

    for column in NUMERIC_FEATURES:
        psi = population_stability_index(reference[column], current[column])
        statistic, pvalue = ks_2samp(reference[column], current[column])
        status = (
            "critical"
            if psi >= float(monitoring["psi_critical"])
            else "warning"
            if psi >= float(monitoring["psi_warning"])
            else "ok"
        )
        numeric[column] = {
            "psi": psi,
            "ks_statistic": float(statistic),
            "ks_pvalue": float(pvalue),
            "status": status,
        }
        if status != "ok" or pvalue < float(monitoring["ks_pvalue"]):
            alerts.append(f"Numeric drift detected for {column}")

    for column in CATEGORICAL_FEATURES:
        tvd = categorical_total_variation(reference[column], current[column])
        status = "warning" if tvd >= float(monitoring["categorical_tvd_warning"]) else "ok"
        categorical[column] = {"total_variation_distance": tvd, "status": status}
        if status != "ok":
            alerts.append(f"Categorical drift detected for {column}")

    prediction: dict[str, Any] | None = None
    if reference_probabilities is not None and current_probabilities is not None:
        delta = abs(float(np.mean(current_probabilities)) - float(np.mean(reference_probabilities)))
        prediction = {
            "reference_mean_probability": float(np.mean(reference_probabilities)),
            "current_mean_probability": float(np.mean(current_probabilities)),
            "absolute_mean_delta": delta,
            "status": (
                "warning" if delta >= float(monitoring["prediction_mean_delta_warning"]) else "ok"
            ),
        }
        if prediction["status"] != "ok":
            alerts.append("Prediction distribution drift detected")

    return {
        "status": "alert" if alerts else "ok",
        "alerts": sorted(set(alerts)),
        "numeric_features": numeric,
        "categorical_features": categorical,
        "prediction_drift": prediction,
    }
