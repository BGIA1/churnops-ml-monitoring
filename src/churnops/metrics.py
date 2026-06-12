"""Classification metric calculation and reporting."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    matrix = confusion_matrix(y_true, predictions, labels=[0, 1])
    true_negative, false_positive, false_negative, true_positive = matrix.ravel()
    roc_auc = float(roc_auc_score(y_true, probabilities)) if len(np.unique(y_true)) > 1 else None
    return {
        "roc_auc": roc_auc,
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "threshold": float(threshold),
        "confusion_matrix": matrix.tolist(),
        "true_negative": int(true_negative),
        "false_positive": int(false_positive),
        "false_negative": int(false_negative),
        "true_positive": int(true_positive),
        "error_explanation": {
            "false_positive": (
                "Active customers incorrectly flagged as likely churners; this may waste "
                "retention budget."
            ),
            "false_negative": (
                "Customers who churned but were not flagged; this represents missed "
                "retention opportunities."
            ),
        },
    }
