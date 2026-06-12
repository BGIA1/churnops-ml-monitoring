# Demo

`churnops demo` resets generated runtime state and performs data generation, Dummy baseline,
Logistic Regression baseline promotion, Random Forest challenger evaluation, API TestClient
validation, batch scoring, drift detection, labeled performance monitoring, controlled
retraining, and static site generation.

The command is deterministic in data, splitting, and model seeds. Registry timestamps and
request IDs are intentionally unique. It requires no permanent server, network dataset, cloud
credentials, or paid service.

The equivalent manual training steps use `--model logistic_regression` for the baseline and
`--model random_forest` for the candidate. Friendly aliases `baseline` and `candidate` are also
accepted by the CLI and normalize to those canonical names.
