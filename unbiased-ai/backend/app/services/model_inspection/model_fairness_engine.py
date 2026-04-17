"""
Model Fairness Inspection Engine (Layer 2)
==========================================

Inspects trained classification models for bias and fairness violations.

Designed to mirror the interface and reporting style of FairnessAuditEngine
(Layer 1), so both layers can be merged into a unified fairness audit pipeline.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Any, Protocol, runtime_checkable


# ──────────────────────────────────────────────────────────────────────────────
# Thresholds
# ──────────────────────────────────────────────────────────────────────────────

DEMOGRAPHIC_PARITY_DIFF_THRESHOLD = 0.10
EQUAL_OPPORTUNITY_DIFF_THRESHOLD = 0.10
EQUALIZED_ODDS_DIFF_THRESHOLD = 0.10
DISPARATE_IMPACT_THRESHOLD = 0.80
SELECTION_RATE_DIFF_THRESHOLD = 0.10

SUBGROUP_ACCURACY_FLOOR = 0.60
MIN_GROUP_SIZE_WARNING = 30
CRITICAL_MIN_GROUP_SIZE = 5


# ──────────────────────────────────────────────────────────────────────────────
# Shared Data Classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class FairnessMetricResult:
    sensitive_attribute: str
    metric_name: str
    value: float
    threshold: float
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class BiasFindingResult:
    finding_type: str
    severity: str
    attribute: str
    description: str
    recommendation: str
    raw_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubgroupPerformance:
    sensitive_attribute: str
    group: str
    n_samples: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    fpr: float
    fnr: float
    confusion_matrix: dict[str, int]


@dataclass
class ModelAuditResult:
    metrics: list[FairnessMetricResult] = field(default_factory=list)
    findings: list[BiasFindingResult] = field(default_factory=list)
    subgroup_performance: list[SubgroupPerformance] = field(default_factory=list)
    overall_risk_score: float = 0.0
    executive_summary: str = ""
    model_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "layer": "model_inspection",
            "overall_risk_score": self.overall_risk_score,
            "executive_summary": self.executive_summary,
            "model_meta": self.model_meta,
            "metrics": [asdict(m) for m in self.metrics],
            "findings": [asdict(f) for f in self.findings],
            "subgroup_performance": [asdict(s) for s in self.subgroup_performance],
        }


# ──────────────────────────────────────────────────────────────────────────────
# Protocol
# ──────────────────────────────────────────────────────────────────────────────

@runtime_checkable
class SklearnClassifier(Protocol):
    def predict(self, X) -> np.ndarray: ...


# ──────────────────────────────────────────────────────────────────────────────
# Engine
# ──────────────────────────────────────────────────────────────────────────────

class ModelFairnessEngine:
    def __init__(
        self,
        model: SklearnClassifier,
        df: pd.DataFrame,
        target_column: str,
        sensitive_columns: list[str],
        positive_label: int | str = 1,
        feature_columns: list[str] | None = None,
    ):
        self.model = model
        self.df = df.copy()
        self.target = target_column
        self.sensitive_cols = sensitive_columns
        self.positive_label = positive_label
        self.feature_columns = feature_columns

        self.result = ModelAuditResult()
        self._y_pred: np.ndarray | None = None
        self._y_true: np.ndarray | None = None

    # ──────────────────────────────────────────────────────────────────────────
    # Public entry point
    # ──────────────────────────────────────────────────────────────────────────

    def run(self) -> ModelAuditResult:
        if not self._validate_inputs():
            self.result.overall_risk_score = self._compute_risk_score()
            self.result.executive_summary = self._build_executive_summary()
            return self.result

        self._generate_predictions()

        if self._y_pred is None or self._y_true is None:
            self.result.overall_risk_score = self._compute_risk_score()
            self.result.executive_summary = self._build_executive_summary()
            return self.result

        self._collect_model_meta()

        for attr in self.sensitive_cols:
            if attr not in self.df.columns:
                self._flag_missing_attribute(attr)
                continue

            self._check_small_groups(attr)
            self._compute_subgroup_performance(attr)
            self._check_demographic_parity(attr)
            self._check_equal_opportunity(attr)
            self._check_equalized_odds(attr)
            self._check_disparate_impact(attr)
            self._check_selection_rate_difference(attr)
            self._check_subgroup_accuracy_floor(attr)

        self.result.overall_risk_score = self._compute_risk_score()
        self.result.executive_summary = self._build_executive_summary()
        return self.result

    # ──────────────────────────────────────────────────────────────────────────
    # Validation
    # ──────────────────────────────────────────────────────────────────────────

    def _validate_inputs(self) -> bool:
        ok = True

        if not isinstance(self.df, pd.DataFrame) or self.df.empty:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="critical",
                attribute="dataset",
                description="Input DataFrame is empty or invalid.",
                recommendation="Provide a non-empty test dataset DataFrame.",
            ))
            return False

        if self.target not in self.df.columns:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="critical",
                attribute=self.target,
                description=f"Target column '{self.target}' not found in DataFrame.",
                recommendation="Verify the target_column matches the test CSV header.",
            ))
            ok = False

        if not callable(getattr(self.model, "predict", None)):
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="critical",
                attribute="model",
                description="Provided model does not implement predict().",
                recommendation="Pass a trained scikit-learn (or compatible) classifier.",
            ))
            ok = False

        if not self.sensitive_cols:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="high",
                attribute="sensitive_columns",
                description="No sensitive attributes were provided for fairness inspection.",
                recommendation="Pass one or more protected attributes (e.g., gender, race, age_group).",
            ))
            ok = False

        if ok and not self._validate_binary_target():
            ok = False

        if ok:
            feat_cols = self._get_feature_columns()
            if not feat_cols:
                self.result.findings.append(BiasFindingResult(
                    finding_type="configuration",
                    severity="critical",
                    attribute="features",
                    description="No feature columns available for prediction.",
                    recommendation="Ensure the dataset contains model feature columns.",
                ))
                ok = False

        return ok

    def _validate_binary_target(self) -> bool:
        unique_vals = pd.Series(self.df[self.target]).dropna().unique().tolist()
        if len(unique_vals) > 2:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="critical",
                attribute=self.target,
                description=f"Target column '{self.target}' appears to be multiclass: {unique_vals}",
                recommendation=(
                    "This engine currently supports binary classification only. "
                    "Provide a binary target or extend the engine for multiclass fairness."
                ),
                raw_data={"unique_target_values": unique_vals},
            ))
            return False
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Prediction generation
    # ──────────────────────────────────────────────────────────────────────────

    def _get_feature_columns(self) -> list[str]:
        if self.feature_columns:
            return self.feature_columns
        return [c for c in self.df.columns if c != self.target]

    def _generate_predictions(self):
        feat_cols = self._get_feature_columns()

        missing_cols = [c for c in feat_cols if c not in self.df.columns]
        if missing_cols:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="critical",
                attribute="features",
                description=f"Missing required feature columns: {missing_cols}",
                recommendation="Ensure the test dataset matches the model training schema.",
                raw_data={"missing_columns": missing_cols},
            ))
            return

        X = self.df[feat_cols]
        self._y_true = self.df[self.target].values

        try:
            y_pred = self.model.predict(X)
            y_pred = np.asarray(y_pred).reshape(-1)
            self._y_pred = y_pred
        except Exception as e:
            self.result.findings.append(BiasFindingResult(
                finding_type="prediction_failure",
                severity="critical",
                attribute="model_prediction",
                description=f"Model prediction failed: {str(e)}",
                recommendation=(
                    "Ensure the uploaded model and test dataset use the same "
                    "feature schema and preprocessing pipeline."
                ),
                raw_data={
                    "error": str(e),
                    "feature_columns": feat_cols,
                    "n_features_passed": len(feat_cols),
                },
            ))
            self._y_pred = None
            return

        if len(self._y_pred) != len(self.df):
            self.result.findings.append(BiasFindingResult(
                finding_type="prediction_failure",
                severity="critical",
                attribute="model_prediction",
                description=(
                    f"Prediction length mismatch: model returned {len(self._y_pred)} "
                    f"predictions for {len(self.df)} rows."
                ),
                recommendation="Verify model integrity and test dataset compatibility.",
                raw_data={
                    "n_predictions": int(len(self._y_pred)),
                    "n_rows": int(len(self.df)),
                },
            ))
            self._y_pred = None
            return

        self.df["__y_pred__"] = self._y_pred

    # ──────────────────────────────────────────────────────────────────────────
    # Model metadata
    # ──────────────────────────────────────────────────────────────────────────

    def _collect_model_meta(self):
        meta: dict[str, Any] = {
            "model_type": type(self.model).__name__,
            "n_test_samples": int(len(self.df)),
            "positive_label": self.positive_label,
            "feature_columns": self._get_feature_columns(),
            "n_sensitive_attributes": len(self.sensitive_cols),
            "sensitive_attributes": self.sensitive_cols,
        }

        y_true = self._y_true
        y_pred = self._y_pred
        pos = self.positive_label

        tp = int(np.sum((y_true == pos) & (y_pred == pos)))
        fp = int(np.sum((y_true != pos) & (y_pred == pos)))
        tn = int(np.sum((y_true != pos) & (y_pred != pos)))
        fn = int(np.sum((y_true == pos) & (y_pred != pos)))

        precision = self._safe_div(tp, tp + fp)
        recall = self._safe_div(tp, tp + fn)
        f1 = self._safe_div(2 * precision * recall, precision + recall)

        meta["global_confusion_matrix"] = {"tp": tp, "fp": fp, "tn": tn, "fn": fn}
        meta["global_accuracy"] = round(float((tp + tn) / len(y_true)), 4) if len(y_true) else 0.0
        meta["global_precision"] = round(precision, 4)
        meta["global_recall"] = round(recall, 4)
        meta["global_f1"] = round(f1, 4)
        meta["n_subgroup_records"] = 0

        self.result.model_meta = meta

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _safe_div(self, num: float, den: float, fallback: float = 0.0) -> float:
        return float(num / den) if den else fallback

    def _normalize_group(self, group: Any) -> str:
        return "MISSING" if pd.isna(group) else str(group)

    def _series_to_group_dict(self, s: pd.Series) -> dict[str, float]:
        return {self._normalize_group(k): round(float(v), 4) for k, v in s.items()}

    def _group_confusion(self, grp_df: pd.DataFrame) -> dict[str, int]:
        pos = self.positive_label
        y_t = grp_df[self.target].values
        y_p = grp_df["__y_pred__"].values

        tp = int(np.sum((y_t == pos) & (y_p == pos)))
        fp = int(np.sum((y_t != pos) & (y_p == pos)))
        tn = int(np.sum((y_t != pos) & (y_p != pos)))
        fn = int(np.sum((y_t == pos) & (y_p != pos)))

        return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}

    # ──────────────────────────────────────────────────────────────────────────
    # Subgroup performance
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_subgroup_performance(self, attr: str):
        for group, grp_df in self.df.groupby(attr, dropna=False):
            group_name = self._normalize_group(group)
            cm = self._group_confusion(grp_df)
            tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
            n = len(grp_df)

            accuracy = self._safe_div(tp + tn, n)
            precision = self._safe_div(tp, tp + fp)
            recall = self._safe_div(tp, tp + fn)
            f1 = self._safe_div(2 * precision * recall, precision + recall)
            fpr = self._safe_div(fp, fp + tn)
            fnr = self._safe_div(fn, fn + tp)

            self.result.subgroup_performance.append(SubgroupPerformance(
                sensitive_attribute=attr,
                group=group_name,
                n_samples=int(n),
                accuracy=round(accuracy, 4),
                precision=round(precision, 4),
                recall=round(recall, 4),
                f1=round(f1, 4),
                fpr=round(fpr, 4),
                fnr=round(fnr, 4),
                confusion_matrix=cm,
            ))

        self.result.model_meta["n_subgroup_records"] = len(self.result.subgroup_performance)

    # ──────────────────────────────────────────────────────────────────────────
    # Fairness metric checks
    # ──────────────────────────────────────────────────────────────────────────

    def _check_demographic_parity(self, attr: str):
        pos = self.positive_label
        sel_rates = self.df.groupby(attr, dropna=False)["__y_pred__"].apply(
            lambda s: (s == pos).mean()
        )

        if len(sel_rates) < 2:
            return

        diff = float(sel_rates.max() - sel_rates.min())
        passed = diff <= DEMOGRAPHIC_PARITY_DIFF_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="demographic_parity_difference",
            value=round(diff, 4),
            threshold=DEMOGRAPHIC_PARITY_DIFF_THRESHOLD,
            passed=passed,
            details=self._series_to_group_dict(sel_rates),
        ))

        if not passed:
            worst_group = self._normalize_group(sel_rates.idxmin())
            self.result.findings.append(BiasFindingResult(
                finding_type="demographic_parity_failure",
                severity="high" if diff > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"Demographic Parity Difference for '{attr}' is {diff:.1%}. "
                    f"Group '{worst_group}' has the lowest selection rate "
                    f"({sel_rates.min():.1%} vs {sel_rates.max():.1%})."
                ),
                recommendation=(
                    "Review the model's decision boundary and training distribution. "
                    "Consider threshold adjustment, re-weighting, or fairness-aware retraining."
                ),
                raw_data=self._series_to_group_dict(sel_rates),
            ))

    def _check_equal_opportunity(self, attr: str):
        pos = self.positive_label
        positives = self.df[self.df[self.target] == pos]

        if positives.empty:
            return

        tpr = positives.groupby(attr, dropna=False)["__y_pred__"].apply(
            lambda s: (s == pos).mean()
        )

        if len(tpr) < 2:
            return

        diff = float(tpr.max() - tpr.min())
        passed = diff <= EQUAL_OPPORTUNITY_DIFF_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="equal_opportunity_difference",
            value=round(diff, 4),
            threshold=EQUAL_OPPORTUNITY_DIFF_THRESHOLD,
            passed=passed,
            details=self._series_to_group_dict(tpr),
        ))

        if not passed:
            worst_group = self._normalize_group(tpr.idxmin())
            self.result.findings.append(BiasFindingResult(
                finding_type="equal_opportunity_failure",
                severity="high" if diff > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"Equal Opportunity Difference for '{attr}' is {diff:.1%}. "
                    f"The model is less likely to correctly identify positive cases "
                    f"for group '{worst_group}'."
                ),
                recommendation=(
                    "Investigate feature quality, representation, and label quality by subgroup. "
                    "Consider threshold calibration or fairness-aware retraining."
                ),
                raw_data=self._series_to_group_dict(tpr),
            ))

    def _check_equalized_odds(self, attr: str):
        pos = self.positive_label
        positives = self.df[self.df[self.target] == pos]
        negatives = self.df[self.df[self.target] != pos]

        if positives.empty or negatives.empty:
            return

        tpr = positives.groupby(attr, dropna=False)["__y_pred__"].apply(
            lambda s: (s == pos).mean()
        )
        fpr = negatives.groupby(attr, dropna=False)["__y_pred__"].apply(
            lambda s: (s == pos).mean()
        )

        if len(tpr) < 2 or len(fpr) < 2:
            return

        tpr_diff = float(tpr.max() - tpr.min())
        fpr_diff = float(fpr.max() - fpr.min())
        eq_odds = round(max(tpr_diff, fpr_diff), 4)
        passed = eq_odds <= EQUALIZED_ODDS_DIFF_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="equalized_odds_difference",
            value=eq_odds,
            threshold=EQUALIZED_ODDS_DIFF_THRESHOLD,
            passed=passed,
            details={
                "tpr_by_group": self._series_to_group_dict(tpr),
                "fpr_by_group": self._series_to_group_dict(fpr),
                "tpr_diff": round(tpr_diff, 4),
                "fpr_diff": round(fpr_diff, 4),
            },
        ))

        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="equalized_odds_failure",
                severity="high" if eq_odds > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"Equalized Odds Difference for '{attr}' is {eq_odds:.1%} "
                    f"(TPR gap={tpr_diff:.1%}, FPR gap={fpr_diff:.1%})."
                ),
                recommendation=(
                    "The model's error rates differ substantially across groups. "
                    "Consider equalized-odds post-processing, re-weighting, or fairness-constrained retraining."
                ),
                raw_data={
                    "tpr_diff": round(tpr_diff, 4),
                    "fpr_diff": round(fpr_diff, 4),
                },
            ))

    def _check_disparate_impact(self, attr: str):
        pos = self.positive_label
        sel_rates = self.df.groupby(attr, dropna=False)["__y_pred__"].apply(
            lambda s: (s == pos).mean()
        )

        if len(sel_rates) < 2 or sel_rates.max() == 0:
            return

        di = round(float(sel_rates.min() / sel_rates.max()), 4)
        passed = di >= DISPARATE_IMPACT_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="disparate_impact",
            value=di,
            threshold=DISPARATE_IMPACT_THRESHOLD,
            passed=passed,
            details=self._series_to_group_dict(sel_rates),
        ))

        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="disparate_impact_failure",
                severity="high" if di < 0.60 else "medium",
                attribute=attr,
                description=(
                    f"Disparate Impact for '{attr}' is {di:.2f}, "
                    f"below the 80% (0.80) threshold."
                ),
                recommendation=(
                    "The model may present adverse-impact risk. "
                    "Audit training data for historical bias and review feature selection."
                ),
                raw_data=self._series_to_group_dict(sel_rates),
            ))

    def _check_selection_rate_difference(self, attr: str):
        pos = self.positive_label
        sel_rates = self.df.groupby(attr, dropna=False)["__y_pred__"].apply(
            lambda s: (s == pos).mean()
        )

        if len(sel_rates) < 2:
            return

        diff = round(float(sel_rates.max() - sel_rates.min()), 4)
        passed = diff <= SELECTION_RATE_DIFF_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="selection_rate_difference",
            value=diff,
            threshold=SELECTION_RATE_DIFF_THRESHOLD,
            passed=passed,
            details={
                "alias_of": "demographic_parity_difference",
                **self._series_to_group_dict(sel_rates),
            },
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # Subgroup quality floor checks
    # ──────────────────────────────────────────────────────────────────────────

    def _check_subgroup_accuracy_floor(self, attr: str):
        for sp in self.result.subgroup_performance:
            if sp.sensitive_attribute != attr:
                continue

            if sp.accuracy < SUBGROUP_ACCURACY_FLOOR:
                self.result.findings.append(BiasFindingResult(
                    finding_type="subgroup_accuracy_floor_failure",
                    severity="high" if sp.accuracy < 0.50 else "medium",
                    attribute=attr,
                    description=(
                        f"Group '{sp.group}' ({attr}) has accuracy of "
                        f"{sp.accuracy:.1%}, below the {SUBGROUP_ACCURACY_FLOOR:.0%} floor."
                    ),
                    recommendation=(
                        "Investigate whether training data under-represents this group "
                        "or whether features are less predictive for this subgroup."
                    ),
                    raw_data={
                        "group": sp.group,
                        "accuracy": sp.accuracy,
                        "n_samples": sp.n_samples,
                    },
                ))

    # ──────────────────────────────────────────────────────────────────────────
    # Warnings / data reliability
    # ──────────────────────────────────────────────────────────────────────────

    def _check_small_groups(self, attr: str):
        counts = self.df[attr].fillna("MISSING").value_counts(dropna=False)

        for group, count in counts.items():
            if count < MIN_GROUP_SIZE_WARNING:
                if count <= CRITICAL_MIN_GROUP_SIZE:
                    severity = "high"
                elif count < 20:
                    severity = "medium"
                else:
                    severity = "low"

                self.result.findings.append(BiasFindingResult(
                    finding_type="small_sample",
                    severity=severity,
                    attribute=attr,
                    description=(
                        f"Group '{group}' in '{attr}' has only {count} samples. "
                        "Model fairness metrics may be unstable or unreliable."
                    ),
                    recommendation=(
                        "Collect more data for under-represented groups before drawing "
                        "strong fairness conclusions from model predictions."
                    ),
                    raw_data={"group": str(group), "count": int(count)},
                ))

    def _flag_missing_attribute(self, attr: str):
        self.result.findings.append(BiasFindingResult(
            finding_type="missing_sensitive_attribute",
            severity="high",
            attribute=attr,
            description=f"Sensitive attribute '{attr}' not found in the test DataFrame.",
            recommendation=f"Include '{attr}' in the test CSV to enable per-group model fairness evaluation.",
        ))

    # ──────────────────────────────────────────────────────────────────────────
    # Scoring
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_risk_score(self) -> float:
        metric_failures = sum(1 for m in self.result.metrics if not m.passed)
        total_metrics = len(self.result.metrics)
        metric_score = (metric_failures / total_metrics) if total_metrics else 0.0

        severity_weights = {
            "low": 0.05,
            "medium": 0.12,
            "high": 0.22,
            "critical": 0.35,
        }

        finding_score = sum(
            severity_weights.get(f.severity, 0.05) for f in self.result.findings
        )

        return round(min((metric_score * 0.65) + min(finding_score, 0.35), 1.0), 3)

    # ──────────────────────────────────────────────────────────────────────────
    # Executive summary
    # ──────────────────────────────────────────────────────────────────────────

    def _build_executive_summary(self) -> str:
        n_metrics = len(self.result.metrics)
        n_failed = sum(1 for m in self.result.metrics if not m.passed)
        risk = self.result.overall_risk_score

        risk_label = (
            "CRITICAL" if risk >= 0.75 else
            "HIGH" if risk >= 0.50 else
            "MEDIUM" if risk >= 0.25 else
            "LOW"
        )

        severity_counts: dict[str, int] = {}
        for f in self.result.findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        sev_text = ", ".join(
            f"{count} {severity}"
            for severity, count in sorted(severity_counts.items())
        ) or "no notable findings"

        attrs_str = ", ".join(self.sensitive_cols) if self.sensitive_cols else "none"
        model_name = type(self.model).__name__ if self.model is not None else "UnknownModel"

        return (
            f"[Model Layer] Overall Fairness Risk: {risk_label} (score: {risk:.2f}). "
            f"Model: {model_name}. Protected attributes audited: {attrs_str}. "
            f"{n_failed}/{n_metrics} fairness metrics failed. "
            f"Findings: {sev_text}."
        )