# GitHub Actions

`ci.yml` runs lint, format checks, mypy, coverage tests, the deterministic demo, API tests, and
Docker build. `codeql.yml` performs Python analysis. `release-please.yml` prepares releases from
Conventional Commits. `pages.yml` publishes `site/`. `gcp-deploy-manual.yml` is a safe,
manual-only template for future OIDC deployment.

Repository settings should require CI and CodeQL, protect the default branch, and restrict
deployment environments. Replace badge and Pages placeholders only after creating the remote.

