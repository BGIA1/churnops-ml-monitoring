# Drift Detection

Numeric features use Population Stability Index and the two-sample Kolmogorov-Smirnov test.
Categorical features use total variation distance. Prediction drift compares the average
champion churn probability between reference and current batches.

PSI below 0.1 is normally treated as stable, 0.1 to 0.25 as a warning, and 0.25 or greater as
critical in the default config. These are demonstration thresholds, not universal standards.
Multiple tests and small samples can create false alerts; domain calibration is required.

