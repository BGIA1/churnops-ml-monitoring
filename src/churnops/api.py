"""FastAPI inference service backed by the champion registry alias."""

from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from churnops.config import load_config
from churnops.service import get_registry, latest_summary, predict_frame


class PredictionInput(BaseModel):
    tenure_months: Annotated[int, Field(ge=0, le=120)]
    monthly_charges: Annotated[float, Field(ge=10, le=300)]
    total_charges: Annotated[float, Field(ge=0, le=40000)]
    contract_type: Literal["month-to-month", "one-year", "two-year"]
    payment_method_category: Literal["bank-transfer", "credit-card", "electronic-check"]
    support_tickets_30d: Annotated[int, Field(ge=0, le=30)]
    usage_minutes_30d: Annotated[float, Field(ge=0, le=20000)]
    data_usage_gb_30d: Annotated[float, Field(ge=0, le=2000)]
    late_payments_6m: Annotated[int, Field(ge=0, le=6)]
    plan_type: Literal["basic", "standard", "premium"]
    region: Literal["north", "central", "south", "west"]


class PredictionResult(BaseModel):
    prediction: int
    churn_probability: float


class PredictionResponse(PredictionResult):
    model_version: str
    threshold: float
    request_id: str


class BatchPredictionRequest(BaseModel):
    records: Annotated[list[PredictionInput], Field(min_length=1, max_length=1000)]


class BatchPredictionResponse(BaseModel):
    request_id: str
    model_version: str
    threshold: float
    predictions: list[PredictionResult]


def create_app(config: dict[str, Any] | None = None) -> FastAPI:
    runtime_config = config or load_config()
    application = FastAPI(
        title="ChurnOps Inference API",
        version="0.1.0",
        description="Champion-model inference for the ChurnOps local MLOps lifecycle.",
    )

    @application.get("/health")
    def health() -> dict[str, Any]:
        registry = get_registry(runtime_config)
        return {
            "status": "healthy",
            "champion_available": registry.champion_exists(),
        }

    @application.get("/model/info")
    def model_info() -> dict[str, Any]:
        registry = get_registry(runtime_config)
        if not registry.champion_exists():
            raise HTTPException(status_code=503, detail="No champion model is registered")
        version = registry.resolve("champion")
        return {
            "model_version": version,
            "metadata": registry.load_metadata(version),
            "metrics": registry.load_metrics(version),
        }

    @application.post("/predict", response_model=PredictionResponse)
    def predict(payload: PredictionInput) -> PredictionResponse:
        try:
            frame = pd.DataFrame([{"customer_id": "CUST-000001", **payload.model_dump()}])
            predictions, probabilities, version, threshold = predict_frame(runtime_config, frame)
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return PredictionResponse(
            prediction=int(predictions[0]),
            churn_probability=float(probabilities[0]),
            model_version=version,
            threshold=threshold,
            request_id=str(uuid4()),
        )

    @application.post("/predict/batch", response_model=BatchPredictionResponse)
    def predict_batch(payload: BatchPredictionRequest) -> BatchPredictionResponse:
        records = [
            {"customer_id": f"CUST-{index:06d}", **item.model_dump()}
            for index, item in enumerate(payload.records, start=1)
        ]
        try:
            predictions, probabilities, version, threshold = predict_frame(
                runtime_config, pd.DataFrame(records)
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return BatchPredictionResponse(
            request_id=str(uuid4()),
            model_version=version,
            threshold=threshold,
            predictions=[
                PredictionResult(prediction=int(prediction), churn_probability=float(probability))
                for prediction, probability in zip(predictions, probabilities, strict=True)
            ],
        )

    @application.get("/metrics/summary")
    def metrics_summary() -> dict[str, Any]:
        return latest_summary(runtime_config)

    return application


app = create_app()
