#!/usr/bin/env python3
"""
UNBIASED AI — Live Demo Script
================================
Run this to see the full audit pipeline in action.

Usage:
    pip install pandas numpy reportlab
    python demo.py

Outputs:
    ./demo_output/report.json
    ./demo_output/report.pdf
"""

import pandas as pd
import numpy as np
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.app.services.audit.fairness_engine import FairnessAuditEngine
from backend.app.services.report.report_generator import generate_reports

CYAN  = "\033[96m"
GREEN = "\033[92m"
RED   = "\033[91m"
AMBER = "\033[93m"
BOLD  = "\033[1m"
RESET = "\033[0m"

def banner():
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════════════════╗
║         UNBIASED AI — Decision Auditor Demo          ║
║         Fairness · Bias Detection · Reporting        ║
╚══════════════════════════════════════════════════════╝{RESET}
""")

def make_synthetic_dataset(n=1200, seed=42):
    np.random.seed(seed)
    gender = np.random.choice(["Male", "Female", "Non-binary"], n, p=[0.60, 0.35, 0.05])
    race   = np.random.choice(["White", "Black", "Hispanic", "Asian"], n, p=[0.55, 0.20, 0.15, 0.10])
    age    = np.random.randint(22, 65, n)
    income = np.where(gender == "Male",       np.random.normal(70000, 15000, n),
             np.where(gender == "Female",     np.random.normal(60000, 13000, n),
                                              np.random.normal(58000, 12000, n))).astype(int)

    prob = 0.5 + (income - 60000) / 200000
    prob += np.where(race == "White",    0.10, 0)
    prob += np.where(race == "Asian",    0.05, 0)
    prob += np.where(race == "Black",   -0.12, 0)
    prob += np.where(race == "Hispanic",-0.08, 0)
    prob += np.where(gender == "Male",   0.05, 0)
    prob  = np.clip(prob, 0.05, 0.95)

    approved = (np.random.rand(n) < prob).astype(int)
    y_pred   = (np.random.rand(n) < (prob + np.random.normal(0, 0.05, n))).astype(int)

    income_f = income.astype(float)
    income_f[race == "Black"] = np.where(
        np.random.rand((race == "Black").sum()) < 0.15,
        np.nan, income_f[race == "Black"]
    )

    return pd.DataFrame({
        "gender": gender, "race": race, "age": age,
        "income": income_f, "approved": approved, "predicted": y_pred
    })


def print_step(n, title):
    print(f"{CYAN}{BOLD}[{n}]{RESET} {BOLD}{title}{RESET}")


def main():
    banner()

    print_step(1, "Generating synthetic loan dataset...")
    df = make_synthetic_dataset()
    print(f"    {GREEN}✓{RESET} {len(df):,} applicants, {len(df.columns)} features\n")

    print_step(2, "Running Fairness Audit Engine...")
    engine = FairnessAuditEngine(
        df,
        target_column="approved",
        sensitive_columns=["gender", "race"],
        y_pred_column="predicted",
    )
    result = engine.run()
    print(f"    {GREEN}✓{RESET} Audit complete\n")

    risk_color = RED if result.overall_risk_score >= 0.5 else AMBER if result.overall_risk_score >= 0.25 else GREEN
    print(f"    {BOLD}Risk Score:{RESET}  {risk_color}{result.overall_risk_score:.2f} / 1.00{RESET}")
    print(f"    {BOLD}Summary:{RESET}     {result.executive_summary}\n")

    print_step(3, "Fairness Metrics:")
    for m in result.metrics:
        icon = f"{GREEN}✓ PASS{RESET}" if m.passed else f"{RED}✗ FAIL{RESET}"
        print(f"    {icon}  {m.sensitive_attribute:<10} {m.metric_name:<25} value={m.value:.4f}  threshold={m.threshold}")
    print()

    print_step(4, "Bias Findings:")
    sev_colors = {"critical": RED, "high": AMBER, "medium": "\033[33m", "low": GREEN}
    for f in result.findings:
        sc = sev_colors.get(f.severity, "")
        print(f"    {sc}[{f.severity.upper():<8}]{RESET}  {f.finding_type:<20} → {f.attribute}")
        print(f"               {f.description[:90]}...")
    print()

    print_step(5, "Generating PDF + JSON reports...")
    out_dir = "./demo_output"
    json_path, pdf_path = generate_reports(
        result.to_dict(),
        output_dir=out_dir,
        audit_run_id="hackathon-demo",
        project_name="Loan Approval Fairness Audit",
    )
    print(f"    {GREEN}✓{RESET} JSON → {json_path}  ({os.path.getsize(json_path) / 1024:.1f} KB)")
    print(f"    {GREEN}✓{RESET} PDF  → {pdf_path}  ({os.path.getsize(pdf_path) / 1024:.1f} KB)")
    print(f"\n{CYAN}{BOLD}Demo complete. Open demo_output/report.pdf to view the audit report.{RESET}\n")


if __name__ == "__main__":
    main()
