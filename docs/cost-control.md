# Cost Control

Local V1 expected cost is **$0 MXN**. Cloud V1 cost is also **$0** because no deployment is
performed by this repository.

Before future deployment, define billing budgets and alerts, Cloud Run maximum instances,
Cloud Run Job timeouts and retry limits, Artifact Registry cleanup, log retention, bucket
lifecycle policies, and API quotas. Serverless targets are selected for scale-to-zero behavior.

To shut down a future environment, delete Cloud Run services and jobs, Artifact Registry
repositories, Storage buckets and object versions, Secret Manager secrets, service accounts and
workload identity bindings, scheduler triggers, monitoring policies, and retained logs as
required. Review Terraform state before deletion; never run teardown against an unknown project.

