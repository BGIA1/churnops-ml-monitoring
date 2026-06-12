"""Application services shared by the CLI, API, tests, and demo."""

from __future__ import annotations

import hashlib
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from churnops.config import configured_path
from churnops.data import generate_one
from churnops.drift import build_drift_report
from churnops.features import FEATURE_COLUMNS, ID_COLUMN, LABEL_COLUMN
from churnops.io import read_json, write_json, write_text
from churnops.metrics import classification_metrics
from churnops.modeling import PREPROCESSING_VERSION, ModelName, build_pipeline
from churnops.promotion import evaluate_promotion_gate
from churnops.registry import LocalModelRegistry
from churnops.validation import ensure_valid, validate_csv, validate_dataframe


def get_registry(config: dict[str, Any]) -> LocalModelRegistry:
    return LocalModelRegistry(configured_path(config, "registry_dir"))


def _dataset_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train_model(
    config: dict[str, Any],
    *,
    model_name: ModelName,
    data_path: Path | None = None,
) -> dict[str, Any]:
    """Validate data, train a deterministic pipeline, evaluate, and register it."""
    source = data_path or configured_path(config, "training_data")
    reports = configured_path(config, "reports_dir")
    validation_path = reports / f"validation-{source.stem}.json"
    frame, validation = validate_csv(
        source,
        require_label=True,
        report_path=validation_path,
        quarantine_dir=configured_path(config, "quarantine_dir"),
    )
    ensure_valid(validation)

    seed = int(config["project"]["seed"])
    test_size = float(config["training"]["test_size"])
    validation_size = float(config["training"]["validation_size"])
    threshold = float(config["training"]["threshold"])
    features = frame[FEATURE_COLUMNS]
    labels = frame[LABEL_COLUMN].to_numpy()

    x_train_val, x_test, y_train_val, y_test = train_test_split(
        features,
        labels,
        test_size=test_size,
        random_state=seed,
        stratify=labels,
    )
    relative_validation_size = validation_size / (1.0 - test_size)
    x_train, x_validation, y_train, y_validation = train_test_split(
        x_train_val,
        y_train_val,
        test_size=relative_validation_size,
        random_state=seed,
        stratify=y_train_val,
    )
    pipeline = build_pipeline(model_name, config)
    pipeline.fit(x_train, y_train)

    validation_probabilities = pipeline.predict_proba(x_validation)[:, 1]
    test_probabilities = pipeline.predict_proba(x_test)[:, 1]
    validation_metrics = classification_metrics(y_validation, validation_probabilities, threshold)
    test_metrics = classification_metrics(y_test, test_probabilities, threshold)
    metrics = {
        **test_metrics,
        "split": "test",
        "validation_metrics": validation_metrics,
    }
    metadata = {
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_path": str(source),
        "dataset_rows": len(frame),
        "dataset_fingerprint": _dataset_fingerprint(source),
        "preprocessing_version": PREPROCESSING_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "split_rows": {
            "train": len(x_train),
            "validation": len(x_validation),
            "test": len(x_test),
        },
        "validation_report": validation.to_dict(),
    }
    registry = get_registry(config)
    version = registry.register(
        pipeline,
        model_name=model_name,
        metrics=metrics,
        metadata=metadata,
        training_config=config,
    )
    return {"version": version, "model_name": model_name, "metrics": metrics}


def promote_candidate(config: dict[str, Any], version: str | None = None) -> dict[str, Any]:
    """Evaluate a candidate against policy and promote or reject it."""
    registry = get_registry(config)
    candidate_version = registry.resolve(version or "candidate")
    if registry.is_rejected(candidate_version):
        return {
            "promoted": False,
            "version": candidate_version,
            "status": "already_rejected",
            "already_rejected": True,
            "message": "Candidate was already rejected; the immutable rejection record was kept.",
        }
    candidate_metrics = registry.load_metrics(candidate_version)
    champion_metrics = registry.load_metrics("champion") if registry.champion_exists() else None
    gate = evaluate_promotion_gate(
        candidate_metrics,
        config,
        champion=champion_metrics,
        baseline=champion_metrics,
        validation_ok=True,
    )
    if gate.passed:
        previous = registry.resolve("champion") if registry.champion_exists() else None
        registry.promote(candidate_version)
        return {
            "promoted": True,
            "version": candidate_version,
            "status": "promoted",
            "already_rejected": False,
            "previous_champion": previous,
            "gate": gate.to_dict(),
        }
    registry.reject(candidate_version, reasons=gate.reasons, gate=gate.to_dict())
    return {
        "promoted": False,
        "version": candidate_version,
        "status": "rejected",
        "already_rejected": False,
        "gate": gate.to_dict(),
    }


def compare_models(
    config: dict[str, Any],
    candidate: str = "candidate",
    champion: str = "champion",
) -> dict[str, Any]:
    registry = get_registry(config)
    candidate_metrics = registry.load_metrics(candidate)
    champion_metrics = registry.load_metrics(champion)
    return {
        "candidate": registry.resolve(candidate),
        "champion": registry.resolve(champion),
        "metrics": {"candidate": candidate_metrics, "champion": champion_metrics},
        "gate": evaluate_promotion_gate(
            candidate_metrics,
            config,
            champion=champion_metrics,
            baseline=champion_metrics,
        ).to_dict(),
    }


def predict_frame(
    config: dict[str, Any],
    frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, str, float]:
    report = validate_dataframe(frame, require_label=False)
    ensure_valid(report)
    registry = get_registry(config)
    model, version = registry.load_model("champion")
    pipeline = cast(Pipeline, model)
    threshold = float(registry.load_metrics(version)["threshold"])
    probabilities = pipeline.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    return predictions, probabilities, version, threshold


def batch_score(
    config: dict[str, Any],
    *,
    input_path: Path | None = None,
) -> dict[str, Any]:
    source = input_path or configured_path(config, "current_batch")
    reports = configured_path(config, "reports_dir")
    frame, validation = validate_csv(
        source,
        require_label=False,
        report_path=reports / f"validation-{source.stem}.json",
        quarantine_dir=configured_path(config, "quarantine_dir"),
    )
    ensure_valid(validation)
    predictions, probabilities, version, threshold = predict_frame(config, frame)
    scored = frame.copy()
    scored["prediction"] = predictions
    scored["churn_probability"] = probabilities.round(8)
    output = configured_path(config, "scored_dir") / f"{source.stem}-scored.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    scored.to_csv(output, index=False)
    metadata = {
        "input": str(source),
        "output": str(output),
        "rows": len(scored),
        "model_version": version,
        "threshold": threshold,
        "scored_at": datetime.now(UTC).isoformat(),
    }
    report_path = reports / f"batch-score-{source.stem}.json"
    write_json(report_path, metadata)
    return {**metadata, "report": str(report_path)}


def monitor_drift(
    config: dict[str, Any],
    *,
    reference_path: Path | None = None,
    current_path: Path | None = None,
) -> dict[str, Any]:
    reference_source = reference_path or configured_path(config, "training_data")
    current_source = current_path or configured_path(config, "drifted_batch")
    reference, reference_validation = validate_csv(reference_source, require_label=True)
    current, current_validation = validate_csv(current_source, require_label=False)
    ensure_valid(reference_validation)
    ensure_valid(current_validation)
    registry = get_registry(config)
    model, version = registry.load_model("champion")
    pipeline = cast(Pipeline, model)
    reference_probabilities = pipeline.predict_proba(reference[FEATURE_COLUMNS])[:, 1]
    current_probabilities = pipeline.predict_proba(current[FEATURE_COLUMNS])[:, 1]
    report = build_drift_report(
        reference,
        current,
        config,
        reference_probabilities=reference_probabilities,
        current_probabilities=current_probabilities,
    )
    report.update(
        {
            "reference": str(reference_source),
            "current": str(current_source),
            "model_version": version,
            "generated_at": datetime.now(UTC).isoformat(),
        }
    )
    reports = configured_path(config, "reports_dir")
    json_path = reports / "drift-report.json"
    markdown_path = reports / "drift-report.md"
    write_json(json_path, report)
    lines = [
        "# Drift Report",
        "",
        f"- Status: **{report['status']}**",
        f"- Model version: `{version}`",
        f"- Alerts: {len(report['alerts'])}",
        "",
        "## Alerts",
        "",
        *(f"- {alert}" for alert in report["alerts"]),
    ]
    write_text(markdown_path, "\n".join(lines) + "\n")
    return {**report, "json_report": str(json_path), "markdown_report": str(markdown_path)}


def monitor_performance(
    config: dict[str, Any],
    *,
    labeled_path: Path | None = None,
) -> dict[str, Any]:
    source = labeled_path or configured_path(config, "labeled_batch")
    frame, validation = validate_csv(
        source,
        require_label=True,
        quarantine_dir=configured_path(config, "quarantine_dir"),
    )
    ensure_valid(validation)
    registry = get_registry(config)
    model, version = registry.load_model("champion")
    pipeline = cast(Pipeline, model)
    champion_metrics = registry.load_metrics(version)
    threshold = float(champion_metrics["threshold"])
    probabilities = pipeline.predict_proba(frame[FEATURE_COLUMNS])[:, 1]
    current_metrics = classification_metrics(
        frame[LABEL_COLUMN].to_numpy(), probabilities, threshold
    )
    monitoring = config["monitoring"]
    alerts: list[str] = []
    if (
        current_metrics["roc_auc"] is not None
        and champion_metrics["roc_auc"] is not None
        and current_metrics["roc_auc"]
        < champion_metrics["roc_auc"] - float(monitoring["roc_auc_degradation_tolerance"])
    ):
        alerts.append("ROC-AUC degradation exceeds tolerance")
    if current_metrics["f1"] < champion_metrics["f1"] - float(
        monitoring["f1_degradation_tolerance"]
    ):
        alerts.append("F1 degradation exceeds tolerance")
    report = {
        "status": "alert" if alerts else "ok",
        "alerts": alerts,
        "model_version": version,
        "champion_baseline_metrics": champion_metrics,
        "current_metrics": current_metrics,
        "labeled_batch": str(source),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    output = configured_path(config, "reports_dir") / "performance-report.json"
    write_json(output, report)
    write_text(
        output.with_suffix(".md"),
        "# Performance Monitoring\n\n"
        f"- Status: **{report['status']}**\n"
        f"- ROC-AUC: {current_metrics['roc_auc']}\n"
        f"- F1: {current_metrics['f1']}\n"
        f"- Recall: {current_metrics['recall']}\n"
        f"- Alerts: {', '.join(alerts) if alerts else 'none'}\n",
    )
    return {**report, "report": str(output)}


def controlled_retrain(config: dict[str, Any]) -> dict[str, Any]:
    training_result = train_model(
        config,
        model_name="random_forest",
        data_path=configured_path(config, "retraining_data"),
    )
    promotion = promote_candidate(config, training_result["version"])
    result = {"training": training_result, "promotion": promotion}
    write_json(configured_path(config, "reports_dir") / "retraining-report.json", result)
    return result


def clean_generated(config: dict[str, Any], *, include_site: bool = False) -> None:
    """Delete generated runtime artifacts while preserving tracked placeholders."""
    directories = [
        configured_path(config, "training_data").parent,
        configured_path(config, "current_batch").parent,
        configured_path(config, "scored_dir"),
        configured_path(config, "quarantine_dir"),
        configured_path(config, "reports_dir"),
        configured_path(config, "registry_dir") / "versions",
        configured_path(config, "registry_dir") / "rejected",
        configured_path(config, "registry_dir") / "aliases",
    ]
    if include_site:
        directories.append(configured_path(config, "site_dir"))
    for directory in directories:
        if not directory.exists():
            continue
        for child in directory.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


def latest_summary(config: dict[str, Any]) -> dict[str, Any]:
    registry = get_registry(config)
    summary: dict[str, Any] = {
        "champion": None,
        "drift": None,
        "performance": None,
    }
    if registry.champion_exists():
        version = registry.resolve("champion")
        summary["champion"] = {
            "version": version,
            "metrics": registry.load_metrics(version),
            "metadata": registry.load_metadata(version),
        }
    reports = configured_path(config, "reports_dir")
    for key, filename in (
        ("drift", "drift-report.json"),
        ("performance", "performance-report.json"),
    ):
        path = reports / filename
        if path.exists():
            summary[key] = read_json(path)
    return summary


def run_demo(config: dict[str, Any]) -> dict[str, Any]:
    """Execute a deterministic, local-only end-to-end lifecycle."""
    clean_generated(config, include_site=True)
    datasets: dict[str, Path] = {"training_data": generate_one(config, "training_data")}
    dummy = train_model(config, model_name="dummy")
    baseline = train_model(config, model_name="logistic_regression")
    baseline_promotion = promote_candidate(config, baseline["version"])
    if not baseline_promotion["promoted"]:
        raise RuntimeError(
            "The configured logistic baseline did not pass the initial promotion gate"
        )
    candidate = train_model(config, model_name="random_forest")
    comparison = compare_models(config)
    candidate_promotion = promote_candidate(config, candidate["version"])

    from fastapi.testclient import TestClient

    from churnops.api import create_app

    sample = pd.read_csv(datasets["training_data"]).iloc[0].to_dict()
    sample.pop(ID_COLUMN)
    sample.pop(LABEL_COLUMN)
    client = TestClient(create_app(config))
    health_status = client.get("/health").status_code
    prediction_response = client.post("/predict", json=sample)
    if health_status != 200 or prediction_response.status_code != 200:
        raise RuntimeError("API validation failed during demo")

    datasets["current_batch"] = generate_one(config, "current_batch")
    scoring = batch_score(config)
    datasets["drifted_batch"] = generate_one(config, "drifted_batch")
    drift = monitor_drift(config)
    datasets["labeled_batch"] = generate_one(config, "labeled_batch")
    performance = monitor_performance(config)
    datasets["retraining_data"] = generate_one(config, "retraining_data")
    retraining = controlled_retrain(config)

    from churnops.reporting import generate_static_site

    site = generate_static_site(config)
    champion_version = get_registry(config).resolve("champion")
    result = {
        "status": "completed",
        "champion": champion_version,
        "datasets": {key: str(path) for key, path in datasets.items()},
        "dummy": dummy,
        "baseline": baseline,
        "baseline_promotion": baseline_promotion,
        "candidate": candidate,
        "comparison": comparison,
        "candidate_promotion": candidate_promotion,
        "api_validation": {
            "health_status": health_status,
            "prediction_status": prediction_response.status_code,
        },
        "batch_scoring": scoring,
        "drift_status": drift["status"],
        "performance_status": performance["status"],
        "retraining": retraining,
        "site": str(site),
    }
    write_json(configured_path(config, "reports_dir") / "demo-summary.json", result)
    return result
