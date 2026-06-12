# Controlled Retraining

`churnops retrain` validates `data/raw/retraining_dataset.csv`, trains a Random Forest
challenger, records its provenance, and invokes the promotion policy. It never writes over the
champion artifact. A failed gate creates a rejected-candidate record with checks and reasons.

Production scheduling should add idempotency keys, distributed locking, approval policy, and
rollback automation. Cloud Run Jobs is the proposed execution target after those controls and
budget alerts are configured.

