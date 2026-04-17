"""
app/services/audit/pipeline_merger.py
=====================================
Enterprise-grade merger for:
- Layer 1: Dataset Fairness Audit
- Layer 2: Model Fairness Inspection

This module combines both outputs into a single unified structure
used by:
- API responses
- PDF / JSON reporting
- frontend dashboards

Key Features
------------
- Backward-compatible flat views ("metrics", "findings")
- Layer-specific views ("dataset_audit", "model_audit")
- Robust subgroup_performance normalization
- Partial-failure tolerant
- Strong metadata for enterprise reporting

Usage
-----
    from app.services.audit.pipeline_merger import merge_audit_results, run_full_pipeline

    merged = merge_audit_results(layer1_result, layer2_result)

    merged = run_full_pipeline(
        model=clf,
        df=test_df,
        target_column="hired",
        sensitive_columns=["gender", "race"],
        positive_label=1,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Unified Result Object
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class UnifiedAuditResult:
    """
    Unified result object covering:
    - dataset-level fairness (Layer 1)
    - model-level fairness (Layer 2)
    """
    overall_risk_score: float = 0.0
    executive_summary: str = ""

    # Layer 1
    dataset_metrics: list[dict] = field(default_factory=list)
    dataset_findings: list[dict] = field(default_factory=list)

    # Layer 2
    model_metrics: list[dict] = field(default_factory=list)
    model_findings: list[dict] = field(default_factory=list)
    subgroup_performance: list[dict] = field(default_factory=list)
    model_meta: dict[str, Any] = field(default_factory=dict)

    # Unified metadata
    pipeline_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "overall_risk_score": self.overall_risk_score,
            "executive_summary": self.executive_summary,

            # Backward-compatible flat views
            "metrics": self.dataset_metrics + self.model_metrics,
            "findings": self.dataset_findings + self.model_findings,

            # Layer-specific structured views
            "dataset_audit": {
                "metrics": self.dataset_metrics,
                "findings": self.dataset_findings,
            },
            "model_audit": {
                "metrics": self.model_metrics,
                "findings": self.model_findings,
                "subgroup_performance": self.subgroup_performance,
                "model_meta": self.model_meta,
            },

            # Pipeline metadata
            "pipeline_meta": self.pipeline_meta,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Internal Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_result_shape(result: Any, layer_name: str) -> dict[str, Any]:
    """
    Convert result object to dict and validate minimum expected structure.
    """
    if hasattr(result, "to_dict") and callable(result.to_dict):
        result_dict = result.to_dict()
    elif isinstance(result, dict):
        result_dict = result
    else:
        raise TypeError(
            f"{layer_name} result must be a result object with .to_dict() or a dict."
        )

    if not isinstance(result_dict, dict):
        raise TypeError(f"{layer_name} result could not be serialized into a dict.")

    return result_dict


def _tag_items(items: list[dict], source_layer: str) -> list[dict]:
    """
    Add source-layer metadata to metrics / findings for frontend filtering
    and reporting clarity.
    """
    tagged = []
    for item in items:
        if isinstance(item, dict):
            tagged.append({**item, "source_layer": source_layer})
        else:
            tagged.append({"value": item, "source_layer": source_layer})
    return tagged


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _severity_score(findings: list[dict]) -> float:
    """
    Estimate escalation contribution from finding severities.
    """
    weights = {"low": 0.03, "medium": 0.08, "high": 0.15, "critical": 0.25}
    return min(sum(weights.get(str(f.get("severity", "low")).lower(), 0.03) for f in findings), 0.35)


def _normalize_subgroup_performance(items: Any) -> list[dict]:
    """
    Normalize subgroup performance into a stable reporting shape.

    Accepts:
    - list[dict]
    - list[dataclass-like objects]
    - malformed entries (gracefully normalized)

    Output shape:
    [
        {
            "sensitive_attribute": "...",
            "group": "...",
            "n_samples": 0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "fpr": 0.0,
            "fnr": 0.0,
            "confusion_matrix": {"tp":0,"fp":0,"tn":0,"fn":0}
        }
    ]
    """
    if not isinstance(items, list):
        return []

    normalized: list[dict] = []

    for item in items:
        if hasattr(item, "__dict__"):
            item = vars(item)

        if not isinstance(item, dict):
            item = {"group": str(item)}

        cm = item.get("confusion_matrix", {})
        if not isinstance(cm, dict):
            cm = {}

        normalized.append({
            "sensitive_attribute": str(item.get("sensitive_attribute", item.get("attribute", "Unknown"))),
            "group": str(item.get("group", "Unknown")),
            "n_samples": int(_safe_float(item.get("n_samples", item.get("count", 0)), 0)),
            "accuracy": round(_safe_float(item.get("accuracy", 0.0)), 4),
            "precision": round(_safe_float(item.get("precision", 0.0)), 4),
            "recall": round(_safe_float(item.get("recall", 0.0)), 4),
            "f1": round(_safe_float(item.get("f1", 0.0)), 4),
            "fpr": round(_safe_float(item.get("fpr", 0.0)), 4),
            "fnr": round(_safe_float(item.get("fnr", 0.0)), 4),
            "confusion_matrix": {
                "tp": int(_safe_float(cm.get("tp", 0), 0)),
                "fp": int(_safe_float(cm.get("fp", 0), 0)),
                "tn": int(_safe_float(cm.get("tn", 0), 0)),
                "fn": int(_safe_float(cm.get("fn", 0), 0)),
            },
        })

    return normalized


def _compute_combined_risk(l1: dict, l2: dict, merged_findings: list[dict]) -> float:
    """
    Compute unified risk score using weighted average + escalation rules.
    """
    l1_score = _safe_float(l1.get("overall_risk_score", 0.0))
    l2_score = _safe_float(l2.get("overall_risk_score", 0.0))

    base = (l1_score * 0.45) + (l2_score * 0.55)
    escalation = _severity_score(merged_findings)

    has_critical = any(str(f.get("severity", "")).lower() == "critical" for f in merged_findings)
    if has_critical:
        base = max(base, 0.65)

    return round(min(base + escalation * 0.25, 1.0), 3)


def _build_combined_summary(l1: dict, l2: dict, combined_risk: float) -> str:
    risk_label = (
        "CRITICAL" if combined_risk >= 0.75 else
        "HIGH" if combined_risk >= 0.50 else
        "MEDIUM" if combined_risk >= 0.25 else
        "LOW"
    )

    l1_summary = l1.get("executive_summary", "No dataset summary available.")
    l2_summary = l2.get("executive_summary", "No model summary available.")

    return (
        f"[Combined Audit] Overall Fairness Risk: {risk_label} "
        f"(score: {combined_risk:.2f}). "
        f"Dataset layer: {l1_summary} "
        f"Model layer: {l2_summary}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Public Merge Function
# ──────────────────────────────────────────────────────────────────────────────

def merge_audit_results(layer1_result: Any, layer2_result: Any) -> UnifiedAuditResult:
    """
    Combine:
    - Layer 1 AuditResult
    - Layer 2 ModelAuditResult

    into a UnifiedAuditResult.
    """
    l1 = _ensure_result_shape(layer1_result, "Layer 1")
    l2 = _ensure_result_shape(layer2_result, "Layer 2")

    dataset_metrics = _tag_items(l1.get("metrics", []), "dataset_audit")
    dataset_findings = _tag_items(l1.get("findings", []), "dataset_audit")
    model_metrics = _tag_items(l2.get("metrics", []), "model_audit")
    model_findings = _tag_items(l2.get("findings", []), "model_audit")

    subgroup_performance = _normalize_subgroup_performance(
        l2.get("subgroup_performance", [])
    )

    merged_findings = dataset_findings + model_findings
    combined_risk = _compute_combined_risk(l1, l2, merged_findings)
    summary = _build_combined_summary(l1, l2, combined_risk)

    return UnifiedAuditResult(
        overall_risk_score=combined_risk,
        executive_summary=summary,
        dataset_metrics=dataset_metrics,
        dataset_findings=dataset_findings,
        model_metrics=model_metrics,
        model_findings=model_findings,
        subgroup_performance=subgroup_performance,
        model_meta=l2.get("model_meta", {}) if isinstance(l2.get("model_meta", {}), dict) else {},
        pipeline_meta={
            "pipeline_version": "2.0-enterprise",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "layers_run": ["dataset_audit", "model_audit"],
            "dataset_metrics_count": len(dataset_metrics),
            "dataset_findings_count": len(dataset_findings),
            "model_metrics_count": len(model_metrics),
            "model_findings_count": len(model_findings),
            "subgroup_count": len(subgroup_performance),
            "partial_success": False,
        },
    )


# ──────────────────────────────────────────────────────────────────────────────
# Convenience: Run Both Layers in One Call
# ──────────────────────────────────────────────────────────────────────────────

def run_full_pipeline(
    model,
    df: pd.DataFrame,
    target_column: str,
    sensitive_columns: list[str],
    positive_label: int | str = 1,
    feature_columns: list[str] | None = None,
    y_pred_column: str | None = None,
) -> UnifiedAuditResult:
    """
    Run:
    - Layer 1 (dataset audit)
    - Layer 2 (model audit)

    Return merged UnifiedAuditResult.
    """
    from app.services.audit.fairness_engine import FairnessAuditEngine
    from app.services.model_inspection.model_fairness_engine import ModelFairnessEngine

    layer1_result = None
    layer2_result = None
    partial_errors: list[str] = []

    # Layer 1
    try:
        layer1_engine = FairnessAuditEngine(
            df=df,
            target_column=target_column,
            sensitive_columns=sensitive_columns,
            positive_label=positive_label,
            y_pred_column=y_pred_column,
        )
        layer1_result = layer1_engine.run()
    except Exception as e:
        partial_errors.append(f"Layer 1 failed: {e}")

    # Layer 2
    try:
        layer2_engine = ModelFairnessEngine(
            model=model,
            df=df,
            target_column=target_column,
            sensitive_columns=sensitive_columns,
            positive_label=positive_label,
            feature_columns=feature_columns,
        )
        layer2_result = layer2_engine.run()
    except Exception as e:
        partial_errors.append(f"Layer 2 failed: {e}")

    if layer1_result is None and layer2_result is None:
        raise RuntimeError(
            f"Full fairness pipeline failed completely. Errors: {' | '.join(partial_errors)}"
        )

    # Fallback if Layer 1 fails
    if layer1_result is None:
        layer1_result = {
            "overall_risk_score": 0.0,
            "executive_summary": "Dataset audit did not complete.",
            "metrics": [],
            "findings": [{
                "finding_type": "layer_failure",
                "severity": "critical",
                "attribute": "dataset_audit",
                "description": partial_errors[0] if partial_errors else "Unknown Layer 1 failure.",
                "recommendation": "Inspect dataset-layer pipeline execution logs.",
            }],
        }

    # Fallback if Layer 2 fails
    if layer2_result is None:
        layer2_result = {
            "overall_risk_score": 0.0,
            "executive_summary": "Model audit did not complete.",
            "metrics": [],
            "findings": [{
                "finding_type": "layer_failure",
                "severity": "critical",
                "attribute": "model_audit",
                "description": partial_errors[-1] if partial_errors else "Unknown Layer 2 failure.",
                "recommendation": "Inspect model-layer pipeline execution logs.",
            }],
            "subgroup_performance": [],
            "model_meta": {},
        }

    merged = merge_audit_results(layer1_result, layer2_result)

    if partial_errors:
        merged.pipeline_meta["partial_success"] = True
        merged.pipeline_meta["partial_errors"] = partial_errors

    return merged