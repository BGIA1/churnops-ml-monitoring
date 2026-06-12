from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi.testclient import TestClient

from churnops.api import create_app
from churnops.config import configured_path
from churnops.data import generate_all
from churnops.features import ID_COLUMN
from churnops.service import promote_candidate, train_model


def _ready_client(config: dict[str, Any]) -> tuple[TestClient, dict[str, Any]]:
    generate_all(config)
    baseline = train_model(config, model_name="logistic_regression")
    assert promote_candidate(config, baseline["version"])["promoted"]
    sample = pd.read_csv(configured_path(config, "current_batch")).iloc[0].to_dict()
    sample.pop(ID_COLUMN)
    return TestClient(create_app(config)), sample


def test_api_health_model_info_and_predictions(test_config: dict[str, Any]) -> None:
    client, sample = _ready_client(test_config)
    assert client.get("/health").json()["champion_available"]
    assert client.get("/model/info").status_code == 200

    response = client.post("/predict", json=sample)
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["churn_probability"] <= 1
    assert payload["model_version"]
    assert payload["request_id"]

    batch = client.post("/predict/batch", json={"records": [sample, sample]})
    assert batch.status_code == 200
    assert len(batch.json()["predictions"]) == 2
    assert client.get("/metrics/summary").status_code == 200


def test_api_rejects_invalid_payload(test_config: dict[str, Any]) -> None:
    client, sample = _ready_client(test_config)
    sample["tenure_months"] = 999
    assert client.post("/predict", json=sample).status_code == 422
