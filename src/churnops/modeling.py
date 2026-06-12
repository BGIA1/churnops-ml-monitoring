"""Versioned sklearn preprocessing and model pipelines."""

from __future__ import annotations

from typing import Any, Literal

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churnops.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES

ModelName = Literal["dummy", "logistic_regression", "random_forest"]
CliModelName = Literal[
    "dummy",
    "logistic_regression",
    "random_forest",
    "baseline",
    "candidate",
]
PREPROCESSING_VERSION = "1.0.0"

MODEL_ALIASES: dict[CliModelName, ModelName] = {
    "dummy": "dummy",
    "logistic_regression": "logistic_regression",
    "random_forest": "random_forest",
    "baseline": "logistic_regression",
    "candidate": "random_forest",
}


def resolve_model_name(model_name: CliModelName) -> ModelName:
    """Resolve friendly CLI names to canonical registered model names."""
    return MODEL_ALIASES[model_name]


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )


def build_pipeline(model_name: ModelName, config: dict[str, Any]) -> Pipeline:
    seed = int(config["project"]["seed"])
    training = config["training"]
    if model_name == "dummy":
        estimator = DummyClassifier(strategy="prior", random_state=seed)
    elif model_name == "logistic_regression":
        estimator = LogisticRegression(
            max_iter=int(training["logistic_max_iter"]),
            random_state=seed,
            class_weight="balanced",
        )
    elif model_name == "random_forest":
        estimator = RandomForestClassifier(
            n_estimators=int(training["random_forest_estimators"]),
            random_state=seed,
            class_weight="balanced",
            min_samples_leaf=3,
            n_jobs=1,
        )
    else:
        raise ValueError(f"Unsupported model: {model_name}")
    return Pipeline([("preprocessor", build_preprocessor()), ("estimator", estimator)])
