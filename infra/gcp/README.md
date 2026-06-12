# GCP Deployment Templates

These files are architecture templates only. They have not been applied and are gated by
`enable_deployment = false` by default. Do not run `terraform apply` until the target project,
IAM, budgets, quotas, data governance, and teardown ownership have been reviewed.

## Target Mapping

- Cloud Run service: FastAPI inference API.
- Cloud Run Jobs: batch scoring, drift monitoring, performance monitoring, and retraining.
- Cloud Storage: versioned datasets, reports, and model artifacts.
- Artifact Registry: container images.
- Secret Manager: future runtime secrets; V1 has none.
- Cloud Logging and Monitoring: structured logs, metrics, alerts, and audit trail.
- GitHub Actions OIDC: short-lived deployment identity without service-account keys.

## Required Future Controls

1. Create a dedicated project and billing budget outside this repository.
2. Configure a workload identity pool/provider and least-privilege deployer service account.
3. Protect the `gcp-production` GitHub environment with required reviewers.
4. Set Cloud Run maximum instances, Job retries/timeouts, bucket lifecycle, and log retention.
5. Review `terraform plan` and container vulnerability results.
6. Apply manually from an approved identity. Never add service-account JSON keys.

The included manual GitHub workflow validates placeholders and stops. It performs no cloud
authentication, plan, apply, push, or deployment.

