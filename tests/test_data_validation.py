from __future__ import annotations

from typing import Any

from churnops.config import configured_path
from churnops.data import generate_all, generate_dataset
from churnops.features import LABEL_COLUMN
from churnops.validation import validate_csv, validate_dataframe


def test_generator_is_deterministic_and_profiles_have_expected_labels() -> None:
    first = generate_dataset(30, seed=7, profile="training")
    second = generate_dataset(30, seed=7, profile="training")
    assert first.equals(second)
    assert LABEL_COLUMN in first
    assert LABEL_COLUMN not in generate_dataset(30, seed=7, profile="current")
    assert first["customer_id"].iloc[0] == "CUST-000001"


def test_generate_all_writes_every_required_dataset(test_config: dict[str, Any]) -> None:
    outputs = generate_all(test_config)
    assert set(outputs) == {
        "training_data",
        "current_batch",
        "drifted_batch",
        "labeled_batch",
        "retraining_data",
    }
    assert all(path.exists() for path in outputs.values())


def test_validation_accepts_valid_data_and_rejects_duplicates(
    test_config: dict[str, Any],
) -> None:
    frame = generate_dataset(40, seed=9, profile="training")
    assert validate_dataframe(frame, require_label=True).valid
    frame.loc[1, "customer_id"] = frame.loc[0, "customer_id"]
    report = validate_dataframe(frame, require_label=True)
    assert not report.valid
    assert any("Duplicate" in error for error in report.critical_errors)

    source = configured_path(test_config, "training_data")
    source.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(source, index=False)
    _, csv_report = validate_csv(
        source,
        require_label=True,
        quarantine_dir=configured_path(test_config, "quarantine_dir"),
    )
    assert not csv_report.valid
    assert list(configured_path(test_config, "quarantine_dir").glob("*.csv"))


def test_validation_rejects_invalid_ranges_and_categories() -> None:
    frame = generate_dataset(20, seed=5, profile="training")
    frame.loc[0, "tenure_months"] = 999
    frame.loc[1, "contract_type"] = "invalid"
    report = validate_dataframe(frame, require_label=True)
    assert not report.valid
    assert len(report.critical_errors) == 2
