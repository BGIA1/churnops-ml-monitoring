from __future__ import annotations

from pathlib import Path
from typing import Any

from churnops.promotion import evaluate_promotion_gate
from churnops.registry import LocalModelRegistry


def _metrics(roc_auc: float = 0.8, f1: float = 0.65, recall: float = 0.7) -> dict[str, Any]:
    return {"roc_auc": roc_auc, "f1": f1, "recall": recall, "threshold": 0.5}


def test_registry_registers_promotes_and_rejects(tmp_path: Path) -> None:
    registry = LocalModelRegistry(tmp_path / "registry")
    version = registry.register(
        {"artifact": "serializable"},
        model_name="test_model",
        metrics=_metrics(),
        metadata={"dataset_rows": 10, "dataset_fingerprint": "abc"},
        training_config={"seed": 42},
    )
    assert registry.resolve("candidate") == version
    registry.promote(version)
    assert registry.resolve("champion") == version
    assert registry.load_model()[0]["artifact"] == "serializable"

    rejected_version = registry.register(
        {"artifact": "rejected"},
        model_name="weak_model",
        metrics=_metrics(0.5, 0.2, 0.1),
        metadata={"dataset_rows": 10},
        training_config={"seed": 42},
    )
    destination = registry.reject(
        rejected_version,
        reasons=["quality gate failed"],
        gate={"passed": False},
    )
    repeated_destination = registry.reject(
        rejected_version,
        reasons=["quality gate failed"],
        gate={"passed": False},
    )
    assert (destination / "rejection_reason.md").exists()
    assert not (destination / "model.joblib").exists()
    assert repeated_destination == destination
    assert registry.is_rejected(rejected_version)


def test_promotion_gate_handles_initial_and_champion_comparisons(
    test_config: dict[str, Any],
) -> None:
    assert evaluate_promotion_gate(_metrics(), test_config).passed
    weak = evaluate_promotion_gate(_metrics(0.4, 0.2, 0.1), test_config)
    assert not weak.passed
    assert "minimum_recall" in weak.checks

    champion = _metrics(0.82, 0.66, 0.72)
    close_candidate = _metrics(0.80, 0.64, 0.70)
    assert evaluate_promotion_gate(
        close_candidate,
        test_config,
        champion=champion,
        baseline=champion,
    ).passed
