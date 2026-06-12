"""Immutable local filesystem model registry."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib

from churnops.io import read_json, write_json, write_text


class LocalModelRegistry:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.versions = root / "versions"
        self.aliases = root / "aliases"
        self.rejected = root / "rejected"
        for directory in (self.versions, self.aliases, self.rejected):
            directory.mkdir(parents=True, exist_ok=True)

    def _new_version(self, model_name: str) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
        return f"{stamp}-{model_name}"

    def register(
        self,
        model: Any,
        *,
        model_name: str,
        metrics: dict[str, Any],
        metadata: dict[str, Any],
        training_config: dict[str, Any],
    ) -> str:
        version = self._new_version(model_name)
        directory = self.versions / version
        directory.mkdir(parents=False, exist_ok=False)
        joblib.dump(model, directory / "model.joblib")
        write_json(directory / "metrics.json", metrics)
        enriched = {**metadata, "version": version, "model_name": model_name}
        write_json(directory / "metadata.json", enriched)
        write_json(directory / "training_config.json", training_config)
        write_text(directory / "model_card.md", self._model_card(enriched, metrics))
        self.set_alias("candidate", version)
        return version

    def _model_card(self, metadata: dict[str, Any], metrics: dict[str, Any]) -> str:
        return (
            f"# Model Card: {metadata['version']}\n\n"
            f"- Model: `{metadata['model_name']}`\n"
            f"- Dataset rows: {metadata.get('dataset_rows', 'unknown')}\n"
            f"- Dataset fingerprint: `{metadata.get('dataset_fingerprint', 'unknown')}`\n"
            f"- ROC-AUC: {metrics.get('roc_auc')}\n"
            f"- F1: {metrics.get('f1')}\n"
            f"- Recall: {metrics.get('recall')}\n"
            f"- Threshold: {metrics.get('threshold')}\n\n"
            "## Intended use\n\n"
            "Synthetic churn risk classification for local MLOps demonstration only.\n\n"
            "## Limitations\n\n"
            "Not trained on real customers, not calibrated for production business decisions, "
            "and not a substitute for fairness, privacy, or domain validation.\n"
        )

    def set_alias(self, alias: str, version: str) -> None:
        if not (self.versions / version).is_dir():
            raise FileNotFoundError(f"Unknown model version: {version}")
        write_json(
            self.aliases / f"{alias}.json",
            {"alias": alias, "version": version, "updated_at": datetime.now(UTC).isoformat()},
        )

    def resolve(self, alias_or_version: str) -> str:
        alias_path = self.aliases / f"{alias_or_version}.json"
        if alias_path.exists():
            return str(read_json(alias_path)["version"])
        if (self.versions / alias_or_version).is_dir():
            return alias_or_version
        raise FileNotFoundError(f"Model alias or version not found: {alias_or_version}")

    def load_model(self, alias_or_version: str = "champion") -> tuple[Any, str]:
        version = self.resolve(alias_or_version)
        return joblib.load(self.versions / version / "model.joblib"), version

    def load_metrics(self, alias_or_version: str) -> dict[str, Any]:
        version = self.resolve(alias_or_version)
        return read_json(self.versions / version / "metrics.json")

    def load_metadata(self, alias_or_version: str) -> dict[str, Any]:
        version = self.resolve(alias_or_version)
        return read_json(self.versions / version / "metadata.json")

    def promote(self, version: str) -> None:
        self.set_alias("champion", version)

    def is_rejected(self, version: str) -> bool:
        """Return whether an immutable rejection record already exists."""
        resolved = self.resolve(version)
        return (self.rejected / resolved).is_dir()

    def reject(
        self,
        version: str,
        *,
        reasons: list[str],
        gate: dict[str, Any],
    ) -> Path:
        source = self.versions / self.resolve(version)
        destination = self.rejected / source.name
        if destination.is_dir():
            return destination
        destination.mkdir(parents=False, exist_ok=False)
        shutil.copy2(source / "metadata.json", destination / "metadata.json")
        shutil.copy2(source / "metrics.json", destination / "metrics.json")
        write_json(destination / "gate_result.json", gate)
        write_text(
            destination / "rejection_reason.md",
            "# Candidate Rejection\n\n" + "\n".join(f"- {reason}" for reason in reasons) + "\n",
        )
        return destination

    def champion_exists(self) -> bool:
        return (self.aliases / "champion.json").exists()
