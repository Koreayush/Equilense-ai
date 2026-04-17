import os
import json
from datetime import datetime

import pandas as pd

from app.services.model_inspection.model_loader import (
    load_model,
    extract_model_metadata,
)
from app.services.model_inspection.inference_runner import run_inference
from app.services.model_inspection.performance_engine import compute_performance_metrics
from app.services.model_inspection.fairness_engine import compute_group_fairness
from app.services.report.report_generator import generate_pdf_report
from app.core.config import settings


# ============================================================
# REPORT OUTPUT CONFIG
# ============================================================

REPORTS_DIR = settings.model_report_dir
os.makedirs(REPORTS_DIR, exist_ok=True)

# REPORTS_DIR = os.path.join("demo_output", "hackathon-demo", "model_audit_reports")
# os.makedirs(REPORTS_DIR, exist_ok=True)


def run_model_audit_pipeline(
    model_path: str,
    eval_csv_path: str,
    target_column: str,
    sensitive_columns: list[str],
    positive_label="1",
):
    # ------------------------------------------------------------
    # Load evaluation data
    # ------------------------------------------------------------
    df = pd.read_csv(eval_csv_path)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")

    for col in sensitive_columns:
        if col not in df.columns:
            raise ValueError(f"Sensitive column '{col}' not found in dataset.")

    positive_label = _coerce_label(positive_label)

    # ------------------------------------------------------------
    # Separate ground truth
    # ------------------------------------------------------------
    y_true = df[target_column]

    # ------------------------------------------------------------
    # Load model
    # ------------------------------------------------------------
    model = load_model(model_path)
    model_meta = extract_model_metadata(model)

    # ------------------------------------------------------------
    # Build inference input
    # IMPORTANT:
    # Keep all columns except target for prediction.
    # Do NOT drop sensitive columns before inference.
    # ------------------------------------------------------------
    X = df.drop(columns=[target_column]).copy()

    # ------------------------------------------------------------
    # Align eval features with model expected input if available
    # ------------------------------------------------------------
    expected_features = _get_expected_model_features(model)

    if expected_features:
        missing_features = [col for col in expected_features if col not in X.columns]
        if missing_features:
            raise ValueError(
                f"Evaluation CSV is missing model-required columns: {missing_features}"
            )

        # Keep only expected columns in correct order
        X = X[expected_features]

    # ------------------------------------------------------------
    # Run inference
    # ------------------------------------------------------------
    y_pred, y_prob = run_inference(model, X, model_path)

    if len(y_pred) != len(df):
        raise ValueError(
            f"Prediction length mismatch: got {len(y_pred)} predictions for {len(df)} rows."
        )

    df["__y_pred__"] = y_pred

    # ------------------------------------------------------------
    # Global model performance
    # ------------------------------------------------------------
    performance = compute_performance_metrics(y_true, y_pred, y_prob)

    # ------------------------------------------------------------
    # Fairness metrics + subgroup performance
    # ------------------------------------------------------------
    fairness_metrics = []
    subgroup_performance = []

    for sensitive_col in sensitive_columns:
        fairness_metrics.extend(
            compute_group_fairness(
                df=df,
                sensitive_col=sensitive_col,
                y_true_col=target_column,
                y_pred_col="__y_pred__",
                positive_label=positive_label,
            )
        )

        subgroup_performance.extend(
            _compute_subgroup_performance(
                df=df,
                sensitive_col=sensitive_col,
                y_true_col=target_column,
                y_pred_col="__y_pred__",
                positive_label=positive_label,
            )
        )

    # ------------------------------------------------------------
    # Findings + Risk
    # ------------------------------------------------------------
    findings = _generate_findings(fairness_metrics)
    risk_score = _compute_risk_score(fairness_metrics)

    # ------------------------------------------------------------
    # Metadata payload
    # ------------------------------------------------------------
    model_meta_payload = {
        **model_meta,
        "n_test_samples": len(df),
        "positive_label": positive_label,
        "global_accuracy": performance.get("accuracy"),
        "global_precision": performance.get("precision"),
        "global_recall": performance.get("recall"),
        "global_f1": performance.get("f1_score"),
        "global_roc_auc": performance.get("roc_auc"),
        "expected_features": expected_features,
    }

    # ------------------------------------------------------------
    # Executive summary
    # ------------------------------------------------------------
    executive_summary = _build_executive_summary(
        performance=performance,
        fairness_metrics=fairness_metrics,
        findings=findings,
        risk_score=risk_score,
    )

    # ------------------------------------------------------------
    # Final result payload
    # ------------------------------------------------------------
    result = {
        "overall_risk_score": risk_score,
        "executive_summary": executive_summary,
        "metrics": fairness_metrics,
        "findings": findings,
        "subgroup_performance": subgroup_performance,
        "model_meta": model_meta_payload,
        "performance": performance,
        "report_urls": {
            "pdf": None,
            "json": None,
        },
    }

    # ------------------------------------------------------------
    # Save reports
    # ------------------------------------------------------------
    report_urls = _save_reports(result)
    result["report_urls"] = report_urls

    return result


# ============================================================
# FEATURE EXTRACTION HELPER
# ============================================================
def _get_expected_model_features(model):
    """
    Try to extract expected input feature names from sklearn models/pipelines.
    Returns list[str] or None.
    """

    # 1) Direct feature_names_in_
    if hasattr(model, "feature_names_in_"):
        try:
            return list(model.feature_names_in_)
        except Exception:
            pass

    # 2) sklearn Pipeline: sometimes first step has feature_names_in_
    if hasattr(model, "named_steps"):
        for _, step in model.named_steps.items():
            if hasattr(step, "feature_names_in_"):
                try:
                    return list(step.feature_names_in_)
                except Exception:
                    continue

    return None


# ============================================================
# REPORT GENERATION
# ============================================================
def _save_reports(result: dict) -> dict:
    """
    Save JSON and PDF reports for Layer 2 audit.
    Returns public URLs usable by frontend.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"model_audit_{timestamp}"

    json_filename = f"{base_name}.json"
    pdf_filename = f"{base_name}.pdf"

    json_path = os.path.join(REPORTS_DIR, json_filename)
    pdf_path = os.path.join(REPORTS_DIR, pdf_filename)

    # Save JSON report
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Save PDF report
    generate_pdf_report(
        result=result,
        pdf_path=pdf_path,
        audit_run_id=base_name,
        project_name="Model Audit"
    )

    return {
        "pdf": f"/reports/model_audit_reports/{pdf_filename}",
        "json": f"/reports/model_audit_reports/{json_filename}",
    }


# ============================================================
# HELPERS
# ============================================================
def _coerce_label(value):
    try:
        return int(value)
    except Exception:
        return value


def _generate_findings(metrics):
    findings = []

    for m in metrics:
        if not m["passed"]:
            findings.append({
                "finding_type": m["metric_name"],
                "severity": _severity_from_metric(m),
                "attribute": m["sensitive_attribute"],
                "description": (
                    f"{m['metric_name'].replace('_', ' ').title()} failed for "
                    f"{m['sensitive_attribute']} with value {m['value']} "
                    f"against threshold {m['threshold']}."
                ),
                "recommendation": (
                    "Review subgroup outcomes, retrain model if needed, inspect proxy "
                    "features, and consider threshold calibration."
                ),
                "raw_data": m.get("details", {})
            })

    return findings


def _severity_from_metric(metric):
    metric_name = metric["metric_name"]
    value = metric["value"]
    threshold = metric["threshold"]

    if metric_name == "disparate_impact":
        if value < 0.5:
            return "critical"
        elif value < 0.65:
            return "high"
        return "medium"

    if value >= threshold + 0.25:
        return "critical"
    elif value >= threshold + 0.15:
        return "high"
    elif value > threshold:
        return "medium"
    return "low"


def _compute_risk_score(metrics):
    if not metrics:
        return 0.0

    failed = sum(1 for m in metrics if not m["passed"])
    return round(failed / len(metrics), 4)


def _build_executive_summary(performance, fairness_metrics, findings, risk_score):
    failed_metrics = sum(1 for m in fairness_metrics if not m["passed"])

    risk_label = (
        "CRITICAL" if risk_score >= 0.8 else
        "HIGH" if risk_score >= 0.6 else
        "MEDIUM" if risk_score >= 0.3 else
        "LOW"
    )

    return (
        f"Model audit completed with {risk_label} fairness risk "
        f"(score: {risk_score}). "
        f"Global accuracy: {performance.get('accuracy', 'N/A')}, "
        f"F1-score: {performance.get('f1_score', 'N/A')}. "
        f"{failed_metrics} fairness checks failed across "
        f"{len(fairness_metrics)} evaluated metrics, generating "
        f"{len(findings)} findings."
    )


def _compute_subgroup_performance(df, sensitive_col, y_true_col, y_pred_col, positive_label=1):
    results = []

    groups = df[sensitive_col].dropna().unique().tolist()

    for group in groups:
        gdf = df[df[sensitive_col] == group]

        if len(gdf) == 0:
            continue

        y_true = gdf[y_true_col]
        y_pred = gdf[y_pred_col]

        tp = ((y_true == positive_label) & (y_pred == positive_label)).sum()
        tn = ((y_true != positive_label) & (y_pred != positive_label)).sum()
        fp = ((y_true != positive_label) & (y_pred == positive_label)).sum()
        fn = ((y_true == positive_label) & (y_pred != positive_label)).sum()

        accuracy = (tp + tn) / len(gdf) if len(gdf) else 0
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0
        fpr = fp / (fp + tn) if (fp + tn) else 0
        fnr = fn / (fn + tp) if (fn + tp) else 0

        results.append({
            "sensitive_attribute": sensitive_col,
            "group": str(group),
            "n_samples": int(len(gdf)),
            "accuracy": round(float(accuracy), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "fpr": round(float(fpr), 4),
            "fnr": round(float(fnr), 4),
        })

    return results