"""
Fairness Audit Engine

Runs statistical bias checks on a dataset and returns structured findings.

Checks implemented:
   - Representation bias
  - Missing bias
  - Label imbalance
  - Demographic parity
  - Disparate impact ratio
  - Equal opportunity (TPR gap)
  - False positive rate parity
  - False negative rate parity
  - Small sample / low-confidence subgroup warnings
  - Missing sensitive attribute warnings
"""

from __future__ import annotations
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Any


# Thresholds 

from app.core.config import settings


DEMOGRAPHIC_PARITY_THRESHOLD = settings.DEMOGRAPHIC_PARITY_WARNING_THRESHOLD 
DISPARATE_IMPACT_THRESHOLD = settings.DISPARATE_IMPACT_THRESHOLD
EQUAL_OPPORTUNITY_WARNING_THRESHOLD = settings.EQUAL_OPPORTUNITY_WARNING_THRESHOLD
REPRESENTATION_IMBALANCE_THRESHOLD = 0.30
FPR_PARITY_THRESHOLD = 0.10                 # max allowed FPR gap
FNR_PARITY_THRESHOLD = 0.10                 # max allowed FNR gap
MISSINGNESS_GAP_THRESHOLD = 0.10            # null-rate spread > 10%
LABEL_IMBALANCE_THRESHOLD = 0.10            # positive-rate spread > 10%
SENSITIVE_NULL_THRESHOLD = 0.05             # >5% null in sensitive attr
MIN_GROUP_SIZE_WARNING = 30


#  Data Structures 

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
class AuditResult:
    metrics: list[FairnessMetricResult] = field(default_factory=list)
    findings: list[BiasFindingResult] = field(default_factory=list)
    overall_risk_score: float = 0.0
    executive_summary: str = ""

    def to_dict(self) -> dict:
        return {
            "overall_risk_score": self.overall_risk_score,
            "executive_summary": self.executive_summary,
            "metrics": [asdict(m) for m in self.metrics],
            "findings": [asdict(f) for f in self.findings],
        }


# Engine 

class FairnessAuditEngine:
    def __init__(
        self,
        df: pd.DataFrame,
        target_column: str,
        sensitive_columns: list[str],
        positive_label=1,
        y_pred_column: str | None = None,
    ):
        self.df = df.copy()
        self.target = target_column
        self.sensitive_cols = sensitive_columns
        self.positive_label = positive_label
        self.y_pred_col = y_pred_column
        self.result = AuditResult()

    def run(self) -> AuditResult:
        self._validate_core_columns()
        
        for attr in self.sensitive_cols:
            if attr not in self.df.columns:
                continue
            
            self._check_sensitive_attribute_missingness(attr)
            self._check_small_group_sizes(attr)
            self._check_representation(attr)
            self._check_missing(attr)
            self._check_label_imbalance(attr)
            self._check_demographic_parity(attr)
            self._check_disparate_impact(attr)
            
            if self._can_run_prediction_metrics():
                self._check_equal_opportunity(attr)
                self._check_false_positive_rate_parity(attr)
                self._check_false_negative_rate_parity(attr)

        self.result.overall_risk_score = self._compute_risk_score()
        self.result.executive_summary = self._build_executive_summary()
        return self.result


    
    # Validation helper 
    
    def _validate_core_columns(self):
        if self.target not in self.df.columns:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="critical",
                attribute=self.target,
                description=(
                    f"Target column '{self.target}' is missing from the dataset."
                ),
                recommendation=(
                    "Ensure the selected target/outcome column exists before running the audit."
                ),
                raw_data={"target_column": self.target},
            ))

        if self.y_pred_col and self.y_pred_col not in self.df.columns:
            self.result.findings.append(BiasFindingResult(
                finding_type="configuration",
                severity="medium",
                attribute=self.y_pred_col,
                description=(
                    f"Prediction column '{self.y_pred_col}' is missing. "
                    "Model fairness metrics could not be evaluated."
                ),
                recommendation=(
                    "Provide a valid prediction column to enable model fairness checks "
                    "such as equal opportunity and error-rate parity."
                ),
                raw_data={"prediction_column": self.y_pred_col},
            ))

    def _can_run_prediction_metrics(self) -> bool:
        return (
            self.target in self.df.columns and
            self.y_pred_col is not None and
            self.y_pred_col in self.df.columns
        )

    # Warning / Meta Checks
    def _add_missing_sensitive_attribute_finding(self, attr: str):
        self.result.findings.append(BiasFindingResult(
            finding_type="missing_sensitive_attribute",
            severity="high",
            attribute=attr,
            description=(
                f"Requested sensitive attribute '{attr}' is missing from the dataset."
            ),
            recommendation=(
                f"Include '{attr}' if legally and ethically appropriate, or document why "
                "fairness could not be assessed for this protected characteristic."
            ),
            raw_data={"attribute": attr},
        ))


    def _check_sensitive_attribute_missingness(self, attr: str):
        null_rate = self.df[attr].isna().mean()
        if null_rate > SENSITIVE_NULL_THRESHOLD:
            severity = "high" if null_rate > 0.20 else "medium"
            self.result.findings.append(BiasFindingResult(
                finding_type="sensitive_attribute_missingness",
                severity=severity,
                attribute=attr,
                description=(
                    f"Sensitive attribute '{attr}' has {null_rate:.1%} missing values."
                ),
                recommendation=(
                    f"Investigate why '{attr}' is incomplete. Missing protected-group data "
                    "can hide fairness issues and reduce audit reliability."
                ),
                raw_data={"null_rate": round(float(null_rate), 4)},
            ))

    def _check_small_group_sizes(self, attr: str):
        counts = self.df[attr].fillna("MISSING").value_counts(dropna=False)
        for group, count in counts.items():
            if count < MIN_GROUP_SIZE_WARNING:
                severity = "high" if count < 10 else "medium" if count < 20 else "low"
                self.result.findings.append(BiasFindingResult(
                    finding_type="small_sample",
                    severity=severity,
                    attribute=attr,
                    description=(
                        f"Group '{group}' in '{attr}' has only {count} samples. "
                        "Fairness metrics for this subgroup may be unstable."
                    ),
                    recommendation=(
                        "Interpret subgroup fairness results with caution. "
                        "Collect more representative data for under-sampled groups."
                    ),
                    raw_data={"group": str(group), "count": int(count)},
                ))


    
    
    #  Dataset Bias Check (Representation )
    def _check_representation(self, attr: str):
        counts = self.df[attr].value_counts()
        max_count = counts.max()
        
        for group, count in counts.items():
            ratio = count / max_count
            
            if ratio < REPRESENTATION_IMBALANCE_THRESHOLD:
                severity = ("critical" if ratio < 0.10 else 
                            "high" if ratio < 0.20 else 
                            "medium")
                
                self.result.findings.append(BiasFindingResult(
                    finding_type="representation",
                    severity=severity,
                    attribute=attr,
                    description=(
                        f"Group '{group}' in '{attr}' is underrepresented: "
                        f"{count} samples ({ratio:.1%} of the largest group)."
                    ),
                    
                    recommendation=(
                        f"Consider collecting more data for '{group}' or applying "
                        "rebalancing techniques. Under-representation can reduce model "
                        "quality and fairness for minority groups."
                    ),
                    
                    raw_data={"group": str(group), 
                              "count": int(count), 
                              "ratio": round(ratio, 4)
                              },
                ))

    #  Missing 
    def _check_missing(self, attr: str):
        
        grouped = self.df.groupby(attr , dropna=False)
        
        for col in self.df.columns:
            if col == attr:
                continue
            
            null_rates = grouped[col].apply(lambda s: s.isna().mean())
            if null_rates.empty:
                continue
            
            spread = float(null_rates.max() - null_rates.min())
            if spread > MISSINGNESS_GAP_THRESHOLD:
                severity = (
                    "high" if spread > 0.25 else
                    "medium" if spread > 0.10 else
                    "low"
                )
                self.result.findings.append(BiasFindingResult(
                    finding_type="missing",
                    severity=severity,
                    attribute=attr,
                    description=(
                        f"Column '{col}' has differential missingness across '{attr}' groups. "
                        f"Null-rate spread is {spread:.1%}."

                    ),
                    recommendation=(
                        f"Investigate why '{col}' is missing more for some groups. "
                        "Imputing without awareness of this gap can introduce bias."
                    ),
                    raw_data={str(k): round(v, 4) 
                              for k, v in null_rates.items()
                              },
                ))

    #  Label Imbalance 
    def _check_label_imbalance(self, attr: str):
        
        if self.target not in self.df.columns:
            return
        
        rates = self.df.groupby(attr, dropna=False)[self.target].apply(
            lambda s: (s == self.positive_label).mean()
        )
        
        if rates.empty:
            return
        
        gap = rates.max() - rates.min()
        
        severity = (
            "critical" if gap > 0.30 else
            "high" if gap > 0.20 else
            "medium" if gap > LABEL_IMBALANCE_THRESHOLD else
            None
        )
        
        if severity:
            self.result.findings.append(BiasFindingResult(
                finding_type="label_imbalance",
                severity=severity,
                attribute=attr,
                description=(
                    f"Positive outcome rates differ by {gap:.1%} across '{attr}' groups."
                ),
                recommendation=(
                    "Large outcome disparities may reflect historical discrimination or "
                    "biased labels. Review whether the target variable is a fair proxy "
                    "for the intended real-world outcome."
                ),
                raw_data={str(k): round(float(v), 4) for k, v in rates.items()},
            ))


    #  Demographic Parity 
    def _check_demographic_parity(self, attr: str):
        
        if self.target not in self.df.columns:
            return
        
        rates = self.df.groupby(attr, dropna=False)[self.target].apply(
            lambda s: (s == self.positive_label).mean()
        )

        if len(rates) < 2:
            return
        
        gap = float(rates.max() - rates.min())
        
        passed = gap <= DEMOGRAPHIC_PARITY_THRESHOLD
        
        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="demographic_parity",
            value=round(gap, 4),
            threshold=DEMOGRAPHIC_PARITY_THRESHOLD,
            passed=passed,
            details={str(k): round(v, 4) for k, v in rates.items()},
        ))
        
        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="demographic_parity_failure",
                severity="high" if gap > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"Demographic parity failed for '{attr}'. "
                    f"Positive outcome rate gap is {gap:.1%}."
                ),
                recommendation=(
                    "Review decision thresholds, label generation, and subgroup representation "
                    "to reduce outcome disparities."
                ),
                raw_data={str(k): round(float(v), 4) for k, v in rates.items()},
            ))


    #  Disparate Impact 
    def _check_disparate_impact(self, attr: str):
        
        if self.target not in self.df.columns:
            return
        
        rates = self.df.groupby(attr, dropna=False)[self.target].apply(
            lambda s: (s == self.positive_label).mean()
        )
        if len(rates) < 2:
            return
        
        max_rate = rates.max()
        if max_rate == 0:
            return
        
        di_ratio = float(rates.min() / max_rate)
        passed = di_ratio >= DISPARATE_IMPACT_THRESHOLD
        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="disparate_impact",
            value=round(di_ratio, 4),
            threshold=DISPARATE_IMPACT_THRESHOLD,
            passed=passed,
            details={str(k): round(v, 4) for k, v in rates.items()},
        ))
        
        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="disparate_impact_failure",
                severity="high" if di_ratio < 0.60 else "medium",
                attribute=attr,
                description=(
                    f"Disparate impact failed for '{attr}'. "
                    f"Impact ratio is {di_ratio:.2f}, below the {DISPARATE_IMPACT_THRESHOLD:.2f} threshold."
                ),
                recommendation=(
                    "Investigate whether one group is receiving substantially fewer positive outcomes. "
                    "Review selection criteria, thresholds, and historical training data."
                ),
                raw_data={str(k): round(float(v), 4) for k, v in rates.items()},
            ))

    #  Equal Opportunity 
    def _check_equal_opportunity(self, attr: str):
        
        positives = self.df[self.df[self.target] == self.positive_label]
        if positives.empty:
            return
        tpr = positives.groupby(attr, dropna=False).apply(
            lambda s: (s[self.y_pred_col] == self.positive_label).mean()
        )

        if len(tpr) < 2:
            return
        
        gap = float(tpr.max() - tpr.min())
        passed = gap <= EQUAL_OPPORTUNITY_WARNING_THRESHOLD
        
        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="equal_opportunity",
            value=round(gap, 4),
            threshold=EQUAL_OPPORTUNITY_WARNING_THRESHOLD,
            passed=passed,
            details={str(k): round(v, 4) for k, v in tpr.items()},
        ))
        
        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="equal_opportunity_failure",
                severity="high" if gap > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"Equal opportunity failed for '{attr}'. "
                    f"True positive rate gap is {gap:.1%}."
                ),
                recommendation=(
                    "The model may correctly identify positive cases for some groups more than others. "
                    "Review training balance, feature quality, and model thresholds."
                ),
                raw_data={str(k): round(float(v), 4) for k, v in tpr.items()},
            ))
            
            
    
    # False Positive Fairness Checks
    def _check_false_positive_rate_parity(self, attr: str):
        negatives = self.df[self.df[self.target] != self.positive_label]
        if negatives.empty:
            return

        fpr = negatives.groupby(attr, dropna=False).apply(
            lambda s: (s[self.y_pred_col] == self.positive_label).mean()
        )

        if len(fpr) < 2:
            return

        gap = float(fpr.max() - fpr.min())
        passed = gap <= FPR_PARITY_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="false_positive_rate_parity",
            value=round(gap, 4),
            threshold=FPR_PARITY_THRESHOLD,
            passed=passed,
            details={str(k): round(float(v), 4) for k, v in fpr.items()},
        ))

        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="false_positive_rate_failure",
                severity="high" if gap > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"False positive rate parity failed for '{attr}'. "
                    f"FPR gap is {gap:.1%}."
                ),
                recommendation=(
                    "Some groups may be incorrectly flagged or incorrectly approved more often than others. "
                    "Review model calibration and decision thresholds."
                ),
                raw_data={str(k): round(float(v), 4) for k, v in fpr.items()},
            ))



    # False Negative Fairness Checks
    def _check_false_negative_rate_parity(self, attr: str):
        positives = self.df[self.df[self.target] == self.positive_label]
        if positives.empty:
            return

        fnr = positives.groupby(attr, dropna=False).apply(
            lambda s: (s[self.y_pred_col] != self.positive_label).mean()
        )

        if len(fnr) < 2:
            return

        gap = float(fnr.max() - fnr.min())
        passed = gap <= FNR_PARITY_THRESHOLD

        self.result.metrics.append(FairnessMetricResult(
            sensitive_attribute=attr,
            metric_name="false_negative_rate_parity",
            value=round(gap, 4),
            threshold=FNR_PARITY_THRESHOLD,
            passed=passed,
            details={str(k): round(float(v), 4) for k, v in fnr.items()},
        ))

        if not passed:
            self.result.findings.append(BiasFindingResult(
                finding_type="false_negative_rate_failure",
                severity="high" if gap > 0.20 else "medium",
                attribute=attr,
                description=(
                    f"False negative rate parity failed for '{attr}'. "
                    f"FNR gap is {gap:.1%}."
                ),
                recommendation=(
                    "Some groups may be denied positive outcomes more often despite being truly eligible. "
                    "Review feature quality, thresholding, and subgroup performance."
                ),
                raw_data={str(k): round(float(v), 4) for k, v in fnr.items()},
            ))
        
        

    #  Scoring 
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
            severity_weights.get(f.severity, 0.05)
            for f in self.result.findings
        )

        # Composite score
        raw_score = (metric_score * 0.65) + min(finding_score, 0.35)

        return round(min(raw_score, 1.0), 3)



    # Executive Summary 
    
    def _build_executive_summary(self) -> str:
        n_metrics = len(self.result.metrics)
        n_failed = sum(1 for m in self.result.metrics if not m.passed)
        n_findings = len(self.result.findings)

        severity_counts = {}
        for f in self.result.findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        risk = self.result.overall_risk_score
        risk_label = (
            "CRITICAL" if risk >= 0.75 else
            "HIGH" if risk >= 0.50 else
            "MEDIUM" if risk >= 0.25 else
            "LOW"
        )

        severity_text = ", ".join(
            f"{count} {severity}"
            for severity, count in sorted(severity_counts.items())
        ) or "no notable findings"

        return (
            f"Overall Fairness Risk: {risk_label} (score: {risk:.2f}). "
            f"{n_failed} of {n_metrics} fairness metrics failed. "
            f"{n_findings} findings detected ({severity_text})."
        )
