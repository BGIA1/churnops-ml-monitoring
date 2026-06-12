# AGENTS.md

## Scope

This repository is a local-first MLOps reference implementation. Keep changes
deterministic, testable, and free of real customer data or credentials.

## Development

- Use Python 3.12 and `uv`.
- Keep application code under `src/churnops`.
- Run `make check` before proposing changes.
- Use Conventional Commits for release automation.
- Do not commit generated datasets, model artifacts, or reports.
- Curated static examples may live under `examples/demo` and `site`.

## Safety

- Never run cloud deployment commands automatically.
- Never add long-lived cloud credentials or API keys.
- Terraform under `infra/gcp` is a non-applied template.
- Preserve champion/challenger controls; retraining must not overwrite a champion blindly.

