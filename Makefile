.PHONY: install lint format typecheck test demo api docker-build clean check

install:
	uv sync --dev

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

test:
	uv run pytest --cov=churnops --cov-report=term-missing

demo:
	uv run churnops demo

api:
	uv run uvicorn churnops.api:app --host 0.0.0.0 --port 8000

docker-build:
	docker build -t churnops-api:local .

clean:
	uv run churnops clean

check: lint typecheck test demo

