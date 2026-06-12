"""Typer command-line interface for the complete local MLOps lifecycle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from churnops.config import load_config
from churnops.data import generate_all
from churnops.modeling import CliModelName, resolve_model_name
from churnops.reporting import generate_static_site
from churnops.service import (
    batch_score,
    clean_generated,
    compare_models,
    controlled_retrain,
    monitor_drift,
    monitor_performance,
    promote_candidate,
    run_demo,
    train_model,
)

app = typer.Typer(
    name="churnops",
    help="Local-first churn MLOps monitoring and controlled retraining.",
    no_args_is_help=True,
)
ConfigOption = Annotated[
    Path,
    typer.Option("--config", help="YAML configuration path.", exists=True, dir_okay=False),
]


def _config(path: Path) -> dict[str, Any]:
    return load_config(path)


def _show(payload: Any) -> None:
    typer.echo(json.dumps(payload, indent=2, default=str))


@app.command("generate-data")
def generate_data(config: ConfigOption = Path("configs/local.yaml")) -> None:
    """Generate deterministic training, inference, drift, monitoring, and retraining data."""
    _show({key: str(value) for key, value in generate_all(_config(config)).items()})


@app.command()
def train(
    model: Annotated[
        CliModelName,
        typer.Option(
            help=(
                "Model to train. baseline maps to logistic_regression; "
                "candidate maps to random_forest."
            )
        ),
    ] = "logistic_regression",
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Validate training data, train a model, evaluate it, and register a candidate."""
    _show(train_model(_config(config), model_name=resolve_model_name(model)))


@app.command()
def evaluate(
    candidate: Annotated[str, typer.Option(help="Candidate alias or version.")] = "candidate",
    champion: Annotated[str, typer.Option(help="Champion alias or version.")] = "champion",
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Compare registered candidate and champion metrics against the promotion gate."""
    _show(compare_models(_config(config), candidate, champion))


@app.command()
def promote(
    version: Annotated[
        str | None, typer.Option(help="Version to promote; defaults to candidate alias.")
    ] = None,
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Promote a candidate only when all configured governance gates pass."""
    _show(promote_candidate(_config(config), version))


@app.command("batch-score")
def batch_score_command(
    input_path: Annotated[
        Path | None, typer.Option("--input", help="CSV batch to validate and score.")
    ] = None,
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Validate and score a batch using the champion model."""
    _show(batch_score(_config(config), input_path=input_path))


@app.command("monitor-drift")
def monitor_drift_command(
    current: Annotated[
        Path | None, typer.Option(help="Current CSV; defaults to generated drifted batch.")
    ] = None,
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Measure numeric, categorical, and prediction drift against training reference data."""
    _show(monitor_drift(_config(config), current_path=current))


@app.command("monitor-performance")
def monitor_performance_command(
    labeled: Annotated[Path | None, typer.Option(help="Labeled monitoring CSV.")] = None,
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Evaluate champion performance on a labeled monitoring batch."""
    _show(monitor_performance(_config(config), labeled_path=labeled))


@app.command()
def retrain(config: ConfigOption = Path("configs/local.yaml")) -> None:
    """Train a challenger on retraining data and promote it only if gates pass."""
    _show(controlled_retrain(_config(config)))


@app.command()
def report(config: ConfigOption = Path("configs/local.yaml")) -> None:
    """Generate a static HTML lifecycle summary under site/."""
    _show({"site": str(generate_static_site(_config(config)))})


@app.command()
def demo(config: ConfigOption = Path("configs/local.yaml")) -> None:
    """Run the deterministic end-to-end local demo, including API validation."""
    result = run_demo(_config(config))
    _show(
        {
            "status": result["status"],
            "champion": result["champion"],
            "drift_status": result["drift_status"],
            "performance_status": result["performance_status"],
            "site": result["site"],
        }
    )


@app.command()
def clean(
    include_site: Annotated[bool, typer.Option(help="Also remove generated site output.")] = False,
    config: ConfigOption = Path("configs/local.yaml"),
) -> None:
    """Remove generated local data, models, aliases, and reports."""
    clean_generated(_config(config), include_site=include_site)
    typer.echo("Generated artifacts removed.")
