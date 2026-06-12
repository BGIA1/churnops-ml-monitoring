from __future__ import annotations

from typing import Any

import pytest

from churnops.config import configured_path
from churnops.service import run_demo


@pytest.mark.integration
def test_deterministic_demo_completes(test_config: dict[str, Any]) -> None:
    result = run_demo(test_config)
    assert result["status"] == "completed"
    assert result["champion"]
    assert result["api_validation"] == {"health_status": 200, "prediction_status": 200}
    assert configured_path(test_config, "site_dir").joinpath("index.html").exists()
    assert configured_path(test_config, "reports_dir").joinpath("demo-summary.json").exists()
