# Local Development

Requirements are Python 3.12, `uv`, and optionally Docker.

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest --cov=churnops
uv run churnops demo
```

For a manual champion/challenger run:

```bash
uv run churnops generate-data
uv run churnops train --model logistic_regression
uv run churnops promote
uv run churnops train --model random_forest
uv run churnops evaluate
uv run churnops promote
```

The canonical names are `logistic_regression` for the baseline and `random_forest` for the
candidate. CLI aliases `baseline` and `candidate` resolve to those canonical values.

Configuration defaults live in `configs/local.yaml`. Generated runtime artifacts are ignored.
Use `uv run churnops clean --include-site` to reset local state.
