"""Deterministic synthetic churn data generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd

from churnops.config import configured_path

Profile = Literal["training", "current", "drifted", "labeled", "retraining"]

DATASET_SPECS: dict[str, tuple[Profile, str, int]] = {
    "training_data": ("training", "training_rows", 0),
    "current_batch": ("current", "batch_rows", 1),
    "drifted_batch": ("drifted", "batch_rows", 2),
    "labeled_batch": ("labeled", "batch_rows", 3),
    "retraining_data": ("retraining", "retraining_rows", 4),
}


def generate_dataset(
    rows: int,
    seed: int,
    profile: Profile = "training",
    *,
    include_label: bool | None = None,
) -> pd.DataFrame:
    """Generate synthetic telecom-like data without real PII."""
    rng = np.random.default_rng(seed)
    drift = profile == "drifted"
    retraining = profile == "retraining"

    tenure_scale = 24 if drift else 34
    tenure = np.clip(rng.gamma(2.0, tenure_scale / 2.0, rows), 0, 120).round().astype(int)
    contract_probs = [0.72, 0.19, 0.09] if drift else [0.54, 0.27, 0.19]
    contract = rng.choice(["month-to-month", "one-year", "two-year"], rows, p=contract_probs)
    plan = rng.choice(
        ["basic", "standard", "premium"],
        rows,
        p=[0.28, 0.45, 0.27] if not drift else [0.18, 0.42, 0.40],
    )
    plan_base = pd.Series(plan).map({"basic": 43.0, "standard": 76.0, "premium": 118.0})
    monthly = (
        plan_base.to_numpy()
        + rng.normal(0, 9, rows)
        + (18 if drift else 0)
        + (4 if retraining else 0)
    )
    monthly = np.clip(monthly, 10, 300).round(2)
    total = np.maximum(0, monthly * tenure + rng.normal(0, 120, rows)).round(2)
    tickets = np.clip(rng.poisson(2.8 if drift else 1.45, rows), 0, 30)
    minutes = np.clip(rng.normal(1300 if drift else 1650, 430, rows), 0, 20000).round(1)
    data_gb = np.clip(rng.gamma(3.5, 7.5 if drift else 5.5, rows), 0, 2000).round(2)
    late = np.clip(rng.binomial(6, 0.28 if drift else 0.13, rows), 0, 6)
    payment = rng.choice(
        ["bank-transfer", "credit-card", "electronic-check"],
        rows,
        p=[0.28, 0.34, 0.38] if drift else [0.34, 0.43, 0.23],
    )
    region = rng.choice(["north", "central", "south", "west"], rows)

    logits = (
        -1.45
        - 0.025 * tenure
        + 0.012 * (monthly - 70)
        + 0.34 * tickets
        + 0.52 * late
        - 0.00035 * minutes
        + 0.60 * (contract == "month-to-month")
        - 0.45 * (contract == "two-year")
        + 0.38 * (payment == "electronic-check")
        + 0.24 * (plan == "premium")
        + 0.30 * (region == "south")
        + rng.normal(0, 0.42, rows)
    )
    probabilities = 1.0 / (1.0 + np.exp(-logits))
    labels = rng.binomial(1, probabilities)

    frame = pd.DataFrame(
        {
            "customer_id": [f"CUST-{index:06d}" for index in range(1, rows + 1)],
            "tenure_months": tenure,
            "monthly_charges": monthly,
            "total_charges": total,
            "contract_type": contract,
            "payment_method_category": payment,
            "support_tickets_30d": tickets,
            "usage_minutes_30d": minutes,
            "data_usage_gb_30d": data_gb,
            "late_payments_6m": late,
            "plan_type": plan,
            "region": region,
            "churn_label": labels,
        }
    )
    should_include_label = (
        include_label
        if include_label is not None
        else profile in {"training", "labeled", "retraining"}
    )
    if not should_include_label:
        frame = frame.drop(columns=["churn_label"])
    return frame


def generate_one(config: dict[str, Any], key: str) -> Path:
    """Generate one configured lifecycle dataset."""
    if key not in DATASET_SPECS:
        raise KeyError(f"Unknown configured dataset: {key}")
    seed = int(config["project"]["seed"])
    profile, rows_key, seed_offset = DATASET_SPECS[key]
    rows = int(config["data"][rows_key])
    destination = configured_path(config, key)
    destination.parent.mkdir(parents=True, exist_ok=True)
    generate_dataset(rows, seed + seed_offset, profile).to_csv(destination, index=False)
    return destination


def generate_all(config: dict[str, Any]) -> dict[str, Path]:
    """Generate all datasets required by the local lifecycle."""
    return {key: generate_one(config, key) for key in DATASET_SPECS}
