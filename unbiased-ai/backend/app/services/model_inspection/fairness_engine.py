import pandas as pd
import numpy as np

DEMOGRAPHIC_PARITY_THRESHOLD = 0.10
DISPARATE_IMPACT_THRESHOLD = 0.80
EQUAL_OPPORTUNITY_THRESHOLD = 0.10
FPR_PARITY_THRESHOLD = 0.10
FNR_PARITY_THRESHOLD = 0.10

def safe_rate(numerator, denominator):
    return float(numerator / denominator) if denominator > 0 else 0.0

def compute_group_fairness(df, sensitive_col, y_true_col, y_pred_col, positive_label=1):
    results = []

    groups = df[sensitive_col].dropna().unique().tolist()
    group_rates = {}

    for group in groups:
        gdf = df[df[sensitive_col] == group]

        approval_rate = safe_rate((gdf[y_pred_col] == positive_label).sum(), len(gdf))
        tpr = safe_rate(((gdf[y_true_col] == positive_label) & (gdf[y_pred_col] == positive_label)).sum(),
                        (gdf[y_true_col] == positive_label).sum())
        fpr = safe_rate(((gdf[y_true_col] != positive_label) & (gdf[y_pred_col] == positive_label)).sum(),
                        (gdf[y_true_col] != positive_label).sum())
        fnr = safe_rate(((gdf[y_true_col] == positive_label) & (gdf[y_pred_col] != positive_label)).sum(),
                        (gdf[y_true_col] == positive_label).sum())

        group_rates[group] = {
            "approval_rate": round(approval_rate, 4),
            "tpr": round(tpr, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
        }

    approval_vals = [v["approval_rate"] for v in group_rates.values()]
    tpr_vals = [v["tpr"] for v in group_rates.values()]
    fpr_vals = [v["fpr"] for v in group_rates.values()]
    fnr_vals = [v["fnr"] for v in group_rates.values()]

    demographic_parity = max(approval_vals) - min(approval_vals) if approval_vals else 0
    disparate_impact = (min(approval_vals) / max(approval_vals)) if max(approval_vals) > 0 else 0
    equal_opportunity = max(tpr_vals) - min(tpr_vals) if tpr_vals else 0
    fpr_parity = max(fpr_vals) - min(fpr_vals) if fpr_vals else 0
    fnr_parity = max(fnr_vals) - min(fnr_vals) if fnr_vals else 0

    results.extend([
        {
            "sensitive_attribute": sensitive_col,
            "metric_name": "demographic_parity",
            "value": round(demographic_parity, 4),
            "threshold": DEMOGRAPHIC_PARITY_THRESHOLD,
            "passed": demographic_parity <= 0.1,
            "details": {k: v["approval_rate"] for k, v in group_rates.items()}
        },
        {
            "sensitive_attribute": sensitive_col,
            "metric_name": "disparate_impact",
            "value": round(disparate_impact, 4),
            "threshold": DISPARATE_IMPACT_THRESHOLD,
            "passed": disparate_impact >= 0.8,
            "details": {k: v["approval_rate"] for k, v in group_rates.items()}
        },
        {
            "sensitive_attribute": sensitive_col,
            "metric_name": "equal_opportunity",
            "value": round(equal_opportunity, 4),
            "threshold": EQUAL_OPPORTUNITY_THRESHOLD,
            "passed": equal_opportunity <= 0.1,
            "details": {k: v["tpr"] for k, v in group_rates.items()}
        },
        {
            "sensitive_attribute": sensitive_col,
            "metric_name": "false_positive_rate_parity",
            "value": round(fpr_parity, 4),
            "threshold": FPR_PARITY_THRESHOLD,
            "passed": fpr_parity <= 0.1,
            "details": {k: v["fpr"] for k, v in group_rates.items()}
        },
        {
            "sensitive_attribute": sensitive_col,
            "metric_name": "false_negative_rate_parity",
            "value": round(fnr_parity, 4),
            "threshold": FNR_PARITY_THRESHOLD,
            "passed": fnr_parity <= 0.1,
            "details": {k: v["fnr"] for k, v in group_rates.items()}
        },
    ])

    return results