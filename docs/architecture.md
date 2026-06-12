# Architecture

ChurnOps separates lifecycle orchestration from interfaces. `service.py` owns use cases;
Typer, FastAPI, tests, and the demo call the same functions. Data generation and validation
are independent of sklearn. The registry owns persistence and aliases. Monitoring consumes
the same feature contract used for training and inference.

The local runtime writes only to `data/`, `models/registry/`, `reports/`, and `site/`.
Generated artifacts are ignored except for curated examples and the static site.

Cloud mapping is intentionally direct: FastAPI to Cloud Run, CLI operations to Cloud Run Jobs,
filesystem artifacts to Cloud Storage, images to Artifact Registry, secrets to Secret Manager,
and logs/metrics to managed observability services.

