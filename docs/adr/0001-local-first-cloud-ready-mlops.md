# ADR 0001: Local-First, Cloud-Ready MLOps

Status: Accepted

ChurnOps runs fully on a developer machine and expresses cloud services as mappings and
templates. This keeps onboarding, CI, cost, and security risk low while preserving deployable
boundaries. The tradeoff is that local filesystem semantics do not provide distributed
coordination.

