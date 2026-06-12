# Security

The project uses synthetic identifiers and contains no real PII. `.env`, data, models, reports,
caches, and local credentials are excluded from source control and Docker build context.
Containers run as a non-root user and Compose uses a read-only filesystem and `no-new-privileges`.

CI uses least permissions. CodeQL and Dependabot configurations are included. Enable GitHub
secret scanning, push protection, branch protection, required reviews, and required checks when
publishing the repository.

Future GCP authentication must use GitHub Actions OIDC and short-lived tokens. Do not create or
store service-account keys. API authentication should use verified identity tokens and explicit
IAM invoker policy.

