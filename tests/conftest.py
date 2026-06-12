from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from churnops.config import load_config


@pytest.fixture
def test_config(tmp_path: Path) -> dict[str, Any]:
    config = copy.deepcopy(load_config())
    config["_project_root"] = str(tmp_path)
    config["data"]["training_rows"] = 500
    config["data"]["batch_rows"] = 90
    config["data"]["retraining_rows"] = 420
    config["training"]["random_forest_estimators"] = 35
    return config
