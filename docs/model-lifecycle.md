# Model Lifecycle

Training validates labeled input, performs seeded stratified train/validation/test splits, and
fits one sklearn pipeline containing preprocessing and estimator. Test metrics are the registry
comparison surface; validation metrics are retained for diagnosis.

The candidate alias points to the latest registered version. Promotion evaluates valid metrics,
data validation, minimum recall, and ROC-AUC/F1 rules. A passing candidate updates the champion
alias. A failing candidate is copied into `rejected/` without a deployable model artifact.
The standard baseline is Logistic Regression (`logistic_regression`) and the standard
challenger is Random Forest (`random_forest`).

Rejection is idempotent. If promotion is requested again for the same rejected version, the
service returns `status: already_rejected`, leaves the rejection artifacts unchanged, and does
not emit a traceback.

Rollback is performed by setting `aliases/champion.json` to a known immutable version using the
registry API after review. Never edit or replace files inside a version directory.
