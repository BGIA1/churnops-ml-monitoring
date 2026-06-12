"""Schema and data-quality validation with quarantine support."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from churnops.features import (
    CATEGORICAL_FEATURES,
    CATEGORY_VALUES,
    FEATURE_COLUMNS,
    ID_COLUMN,
    LABEL_COLUMN,
    NUMERIC_FEATURES,
    NUMERIC_RANGES,
)
from churnops.io import write_json


@dataclass
class ValidationReport:
    valid: bool
    rows: int
    require_label: bool
    critical_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checked_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_dataframe(frame: pd.DataFrame, *, require_label: bool) -> ValidationReport:
    """Validate the feature contract and return a serializable report."""
    errors: list[str] = []
    warnings: list[str] = []
    required = [ID_COLUMN, *FEATURE_COLUMNS]
    if require_label:
        required.append(LABEL_COLUMN)

    missing = sorted(set(required) - set(frame.columns))
    if missing:
        errors.append(f"Missing required columns: {', '.join(missing)}")
        return ValidationReport(False, len(frame), require_label, errors, warnings)

    null_columns = frame[required].columns[frame[required].isnull().any()].tolist()
    if null_columns:
        errors.append(f"Null values found in: {', '.join(null_columns)}")

    if not frame[ID_COLUMN].map(lambda value: isinstance(value, str)).all():
        errors.append("customer_id must contain strings")
    if frame[ID_COLUMN].duplicated().any():
        errors.append("Duplicate customer_id values detected")
    invalid_ids = ~frame[ID_COLUMN].astype(str).str.fullmatch(r"CUST-\d{6}")
    if invalid_ids.any():
        errors.append("customer_id values must match CUST-000001")

    for column in NUMERIC_FEATURES:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            errors.append(f"{column} must be numeric")
            continue
        lower, upper = NUMERIC_RANGES[column]
        outside = ~frame[column].between(lower, upper, inclusive="both")
        if outside.any():
            errors.append(f"{column} contains values outside [{lower}, {upper}]")

    for column in CATEGORICAL_FEATURES:
        invalid = sorted(set(frame[column].dropna().astype(str)) - set(CATEGORY_VALUES[column]))
        if invalid:
            errors.append(f"{column} contains invalid categories: {invalid}")

    if require_label:
        if not pd.api.types.is_numeric_dtype(frame[LABEL_COLUMN]):
            errors.append("churn_label must be numeric")
        elif not frame[LABEL_COLUMN].isin([0, 1]).all():
            errors.append("churn_label must contain only 0 or 1")
        elif frame[LABEL_COLUMN].nunique() < 2:
            warnings.append("churn_label contains only one class")

    unexpected = sorted(set(frame.columns) - set(required))
    if unexpected:
        warnings.append(f"Unexpected columns ignored: {', '.join(unexpected)}")
    return ValidationReport(not errors, len(frame), require_label, errors, warnings)


def validate_csv(
    path: Path,
    *,
    require_label: bool,
    report_path: Path | None = None,
    quarantine_dir: Path | None = None,
) -> tuple[pd.DataFrame, ValidationReport]:
    """Read and validate a CSV, quarantining invalid batches when requested."""
    frame = pd.read_csv(path)
    report = validate_dataframe(frame, require_label=require_label)
    if report_path:
        write_json(report_path, report.to_dict())
    if not report.valid and quarantine_dir:
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        quarantined = quarantine_dir / f"{stamp}-{path.name}"
        frame.to_csv(quarantined, index=False)
        write_json(quarantined.with_suffix(".validation.json"), report.to_dict())
    return frame, report


def ensure_valid(report: ValidationReport) -> None:
    if not report.valid:
        raise ValueError("; ".join(report.critical_errors))
