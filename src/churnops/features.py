"""Shared feature contract for training, monitoring, and inference."""

ID_COLUMN = "customer_id"
LABEL_COLUMN = "churn_label"

NUMERIC_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "support_tickets_30d",
    "usage_minutes_30d",
    "data_usage_gb_30d",
    "late_payments_6m",
]

CATEGORICAL_FEATURES = [
    "contract_type",
    "payment_method_category",
    "plan_type",
    "region",
]

FEATURE_COLUMNS = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]

CATEGORY_VALUES = {
    "contract_type": ["month-to-month", "one-year", "two-year"],
    "payment_method_category": ["bank-transfer", "credit-card", "electronic-check"],
    "plan_type": ["basic", "standard", "premium"],
    "region": ["north", "central", "south", "west"],
}

NUMERIC_RANGES = {
    "tenure_months": (0.0, 120.0),
    "monthly_charges": (10.0, 300.0),
    "total_charges": (0.0, 40000.0),
    "support_tickets_30d": (0.0, 30.0),
    "usage_minutes_30d": (0.0, 20000.0),
    "data_usage_gb_30d": (0.0, 2000.0),
    "late_payments_6m": (0.0, 6.0),
}
