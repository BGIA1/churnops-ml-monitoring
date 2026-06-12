# ADR 0002: Local Model Registry over MLflow Server

Status: Accepted

V1 uses immutable directories plus JSON aliases because the portfolio goal is lifecycle logic,
not operating a tracking server. This makes artifact structure, promotion, rejection, and
rollback visible and testable with no service dependency. A shared deployment should replace
this backend with durable object storage and atomic coordination.

