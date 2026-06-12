# Deployment Readiness

This repository does not deploy infrastructure. `infra/gcp` contains reviewable templates and
the GitHub workflow is `workflow_dispatch` only. Required future inputs include project ID,
region, Artifact Registry repository, workload identity provider, and deployer service account.

The recommended sequence is security review, budget setup, `terraform plan`, peer approval,
manual apply from an authorized environment, image build, vulnerability review, and controlled
service rollout. Production data and model storage need encryption, retention, IAM, and backup
policies beyond this demonstration.

