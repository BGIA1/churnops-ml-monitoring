from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from churnops.cli import app


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("baseline", "logistic_regression"),
        ("candidate", "random_forest"),
    ],
)
def test_train_command_accepts_model_aliases(
    monkeypatch: pytest.MonkeyPatch,
    alias: str,
    canonical: str,
) -> None:
    captured: dict[str, Any] = {}

    def fake_train_model(
        config: dict[str, Any],
        *,
        model_name: str,
    ) -> dict[str, Any]:
        captured["config"] = config
        captured["model_name"] = model_name
        return {"model_name": model_name}

    monkeypatch.setattr("churnops.cli.train_model", fake_train_model)
    result = CliRunner().invoke(
        app,
        ["train", "--model", alias, "--config", "configs/local.yaml"],
    )

    assert result.exit_code == 0
    assert captured["model_name"] == canonical
    assert canonical in result.stdout
