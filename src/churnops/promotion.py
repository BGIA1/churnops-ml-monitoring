"""Champion/challenger promotion policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class GateResult:
    passed: bool
    reasons: list[str]
    checks: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_promotion_gate(
    candidate: dict[str, Any],
    config: dict[str, Any],
    *,
    champion: dict[str, Any] | None = None,
    baseline: dict[str, Any] | None = None,
    validation_ok: bool = True,
) -> GateResult:
    policy = config["promotion"]
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    valid_metrics = all(candidate.get(metric) is not None for metric in ("roc_auc", "f1", "recall"))
    checks["valid_metrics"] = valid_metrics
    checks["validation"] = validation_ok
    checks["minimum_recall"] = float(candidate.get("recall") or 0) >= float(policy["min_recall"])

    if champion is None:
        checks["roc_auc_gate"] = float(candidate.get("roc_auc") or 0) >= float(
            policy["initial_min_roc_auc"]
        )
        checks["f1_gate"] = float(candidate.get("f1") or 0) >= float(policy["initial_min_f1"])
    else:
        candidate_roc = float(candidate.get("roc_auc") or 0)
        candidate_f1 = float(candidate.get("f1") or 0)
        champion_roc = float(champion.get("roc_auc") or 0)
        champion_f1 = float(champion.get("f1") or 0)
        baseline_roc = float((baseline or {}).get("roc_auc") or 0)
        baseline_f1 = float((baseline or {}).get("f1") or 0)
        checks["roc_auc_gate"] = candidate_roc >= champion_roc - float(
            policy["roc_auc_tolerance"]
        ) or candidate_roc >= baseline_roc + float(policy["baseline_roc_auc_min_improvement"])
        checks["f1_gate"] = candidate_f1 >= champion_f1 - float(
            policy["f1_tolerance"]
        ) or candidate_f1 >= baseline_f1 + float(policy["baseline_f1_min_improvement"])

    labels = {
        "valid_metrics": "candidate metrics are missing or invalid",
        "validation": "critical data validation failure",
        "minimum_recall": "candidate recall is below the configured minimum",
        "roc_auc_gate": "candidate ROC-AUC did not satisfy the promotion policy",
        "f1_gate": "candidate F1 did not satisfy the promotion policy",
    }
    for check, passed in checks.items():
        if not passed:
            reasons.append(labels[check])
    return GateResult(all(checks.values()), reasons, checks)
