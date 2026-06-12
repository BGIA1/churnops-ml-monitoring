"""Configuration loading and project path helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG = Path("configs/local.yaml")


def find_project_root(start: Path | None = None) -> Path:
    """Find the nearest directory containing pyproject.toml."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and attach resolved internal metadata."""
    if path is None:
        environment_path = os.getenv("CHURNOPS_CONFIG")
        requested = Path(environment_path) if environment_path else DEFAULT_CONFIG
    else:
        requested = Path(path)
    root = find_project_root()
    config_path = requested if requested.is_absolute() else root / requested
    with config_path.open(encoding="utf-8") as handle:
        config: dict[str, Any] = yaml.safe_load(handle)
    config["_config_path"] = str(config_path.resolve())
    config["_project_root"] = str(root)
    return config


def project_path(config: dict[str, Any], value: str | Path) -> Path:
    """Resolve a configured path against the project root."""
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(config["_project_root"]) / path


def configured_path(config: dict[str, Any], key: str) -> Path:
    """Resolve a key from the paths configuration section."""
    return project_path(config, str(config["paths"][key]))
