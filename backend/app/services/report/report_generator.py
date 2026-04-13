import os
import json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.units import mm


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

def generate_reports(result: dict, output_dir: str, audit_run_id: str, project_name: str):
    """
    Generate JSON + PDF fairness audit reports.
    Returns: (json_path, pdf_path)
    """
    run_dir = os.path.join(output_dir, audit_run_id)
    os.makedirs(run_dir, exist_ok=True)

    json_path = os.path.join(run_dir, f"{audit_run_id}_report.json")
    pdf_path = os.path.join(run_dir, f"{audit_run_id}_report.pdf")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    generate_pdf_report(result, pdf_path, audit_run_id, project_name)
    return json_path, pdf_path


# ─────────────────────────────────────────────────────────────
# MAIN PDF GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_pdf_report(result: dict, pdf_path: str, audit_run_id: str, project_name: str):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = build_styles()
    story = []

    # Unified data
    overall_risk = safe_float(result.get("overall_risk_score", 0))
    executive_summary = result.get("executive_summary", "No executive summary available.")
    metrics = ensure_list(result.get("metrics", []))
    findings = ensure_list(result.get("findings", []))

    # Layer-specific data
    dataset_audit = result.get("dataset_audit", {}) if isinstance(result.get("dataset_audit", {}), dict) else {}
    model_audit = result.get("model_audit", {}) if isinstance(result.get("model_audit", {}), dict) else {}
    pipeline_meta = result.get("pipeline_meta", {}) if isinstance(result.get("pipeline_meta", {}), dict) else {}

    dataset_metrics = ensure_list(dataset_audit.get("metrics", []))
    dataset_findings = ensure_list(dataset_audit.get("findings", []))
    model_metrics = ensure_list(model_audit.get("metrics", []))
    model_findings = ensure_list(model_audit.get("findings", []))
    subgroup_performance = normalize_subgroup_performance(model_audit.get("subgroup_performance", []))
    model_meta = model_audit.get("model_meta", {}) if isinstance(model_audit.get("model_meta", {}), dict) else {}

    # Fallback for standalone model audit
    if not model_metrics and metrics:
        model_metrics = metrics
    if not model_findings and findings:
        model_findings = findings

    risk_label = get_risk_label(overall_risk)
    risk_color = get_risk_color(overall_risk)

    total_metrics = len(metrics)
    failed_metrics = len([m for m in metrics if not m.get("passed", False)])
    total_findings = len(findings)

    critical_count = len([f for f in findings if str(f.get("severity", "")).lower() == "critical"])
    high_count = len([f for f in findings if str(f.get("severity", "")).lower() == "high"])
    medium_count = len([f for f in findings if str(f.get("severity", "")).lower() == "medium"])
    low_count = len([f for f in findings if str(f.get("severity", "")).lower() == "low"])

    # Header
    story.extend(build_header(styles=styles, project_name=project_name, audit_run_id=audit_run_id))
    story.append(Spacer(1, 8))

    # Big risk card
    story.append(build_big_risk_card(
        score=overall_risk,
        label=risk_label,
        color=risk_color,
        failed_metrics=failed_metrics,
        total_metrics=total_metrics,
        total_findings=total_findings,
        styles=styles,
    ))
    story.append(Spacer(1, 14))

    # Executive Summary
    story.append(section_title("Executive Summary", styles))
    story.append(build_info_card(executive_summary, styles))
    story.append(Spacer(1, 14))

    # KPI Snapshot
    story.append(section_title("Audit Snapshot", styles))
    story.append(build_kpi_table(
        [
            ("Risk Score", f"{overall_risk:.2f}", risk_color),
            ("Metrics Failed", f"{failed_metrics} / {total_metrics}", "#DC2626" if failed_metrics else "#16A34A"),
            ("Bias Findings", f"{total_findings}", "#1D4ED8"),
            ("Deployment", get_deployment_status(overall_risk), get_deployment_color(overall_risk)),
        ],
        styles
    ))
    story.append(Spacer(1, 14))

    # Model Overview
    story.append(section_title("Model Audit Overview", styles))
    story.append(build_model_overview_card(model_meta, styles))
    story.append(Spacer(1, 14))

    # Layer Summary
    story.append(section_title("Layer Summary", styles))
    story.append(build_layer_summary_table(
        dataset_metrics=dataset_metrics,
        dataset_findings=dataset_findings,
        model_metrics=model_metrics,
        model_findings=model_findings,
        subgroup_performance=subgroup_performance,
        styles=styles,
    ))
    story.append(Spacer(1, 14))

    # Risk Drivers
    story.append(section_title("Top Fairness Risk Drivers", styles))
    story.append(build_top_risk_drivers(metrics, findings, styles))
    story.append(Spacer(1, 14))

    # Fairness Interpretation
    story.append(section_title("Model Fairness Interpretation", styles))
    story.append(build_info_card(generate_model_interpretation(overall_risk, metrics, findings), styles))
    story.append(Spacer(1, 14))

    # Unified Metrics
    story.append(section_title("Unified Fairness Metrics", styles))
    story.append(Paragraph(
        "Combined fairness indicators from both dataset-level and model-level auditing.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 6))
    story.append(build_metrics_table(metrics, styles))
    story.append(Spacer(1, 16))

    # Dataset Metrics
    story.append(section_title("Dataset Audit Metrics (Layer 1)", styles))
    story.append(Paragraph(
        "Fairness indicators derived directly from the dataset and target distributions.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 6))
    story.append(build_metrics_table(dataset_metrics, styles))
    story.append(Spacer(1, 14))

    # Model Metrics
    story.append(section_title("Model Audit Metrics (Layer 2)", styles))
    story.append(Paragraph(
        "Fairness indicators derived from model predictions and subgroup outcomes.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 6))
    story.append(build_metrics_table(model_metrics, styles))
    story.append(Spacer(1, 16))

    # Findings
    story.append(section_title("Bias Findings", styles))
    story.append(Paragraph(
        "Potential fairness concerns detected during analysis, with severity and recommendations.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 8))

    if findings:
        for idx, finding in enumerate(findings, start=1):
            story.append(build_finding_card(idx, finding, styles))
            story.append(Spacer(1, 10))
    else:
        story.append(build_info_card("No bias findings detected in this audit run.", styles))

    story.append(Spacer(1, 14))

    # Group Breakdown
    story.append(section_title("Group-Level Breakdown", styles))
    story.append(Paragraph(
        "Approval / positive outcome distribution across sensitive attribute groups.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 6))
    story.append(build_group_breakdown_table(metrics, styles))
    story.append(Spacer(1, 18))

    # Subgroup Performance
    story.append(section_title("Subgroup Model Performance", styles))
    story.append(Paragraph(
        "Per-group model performance metrics used to identify subgroup reliability and fairness risks.",
        styles["Muted"]
    ))
    story.append(Spacer(1, 6))
    story.append(build_subgroup_performance_table(subgroup_performance, styles))
    story.append(Spacer(1, 18))

    # Subgroup Risk View
    story.append(section_title("Subgroup Risk Assessment", styles))
    story.append(build_subgroup_risk_table(subgroup_performance, styles))
    story.append(Spacer(1, 18))

    # Model Metadata
    story.append(section_title("Model Audit Metadata", styles))
    story.append(build_model_meta_table(model_meta, styles))
    story.append(Spacer(1, 18))

    # Pipeline Metadata
    story.append(section_title("Pipeline Metadata", styles))
    story.append(build_pipeline_meta_table(pipeline_meta, styles))
    story.append(Spacer(1, 18))

    # Final Assessment
    summary_line = (
        f"This audit detected <b>{total_findings}</b> findings "
        f"(<font color='#DC2626'><b>{critical_count} critical</b></font>, "
        f"<font color='#D97706'><b>{high_count} high</b></font>, "
        f"<font color='#CA8A04'><b>{medium_count} medium</b></font>, "
        f"<font color='#16A34A'><b>{low_count} low</b></font>) and "
        f"<b>{failed_metrics}</b> failed fairness checks out of <b>{total_metrics}</b>."
    )

    story.append(section_title("Final Assessment", styles))
    story.append(build_info_card(summary_line, styles))
    story.append(Spacer(1, 10))

    story.append(section_title("Deployment Recommendation", styles))
    story.append(build_info_card(generate_deployment_recommendation(overall_risk, findings), styles))
    story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#CBD5E1")))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "Generated by <b>Equilense AI — Decision Auditor</b><br/>"
        "Enterprise Fairness · Bias Detection · Reporting",
        styles["Footer"]
    ))

    doc.build(story)


# ─────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────

def build_styles():
    base = getSampleStyleSheet()

    return {
        "TitleMain": ParagraphStyle(
            "TitleMain",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "TitleAccent": ParagraphStyle(
            "TitleAccent",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1D4ED8"),
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "SubTitle": ParagraphStyle(
            "SubTitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "Section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10.3,
            leading=15,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10.3,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_LEFT,
        ),
        "Muted": ParagraphStyle(
            "Muted",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_LEFT,
        ),
        "SmallCenter": ParagraphStyle(
            "SmallCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
        ),
        "RiskScoreBig": ParagraphStyle(
            "RiskScoreBig",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=30,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
        ),
        "RiskLabel": ParagraphStyle(
            "RiskLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "Footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
        ),
    }


# ─────────────────────────────────────────────────────────────
# HEADER / HERO
# ─────────────────────────────────────────────────────────────

def build_header(styles, project_name: str, audit_run_id: str):
    generated_at = datetime.now().strftime("%B %d, %Y • %I:%M %p")

    left_block = [
        Paragraph("Equilense AI", styles["TitleAccent"]),
        Paragraph(project_name, styles["TitleMain"]),
        Paragraph("Fairness · Bias Detection · Reporting", styles["SubTitle"]),
    ]

    right_meta = Paragraph(
        f"<b>Audit Run ID:</b> {audit_run_id}<br/>"
        f"<b>Generated:</b> {generated_at}",
        styles["Body"]
    )

    table = Table([[left_block, right_meta]], colWidths=[340, 150])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))

    return [table]


# ─────────────────────────────────────────────────────────────
# BIG RISK CARD
# ─────────────────────────────────────────────────────────────

def build_big_risk_card(score, label, color, failed_metrics, total_metrics, total_findings, styles):
    left = [
        Paragraph("Overall Fairness Risk", styles["Muted"]),
        Spacer(1, 4),
        Paragraph(f"{score:.2f}", styles["RiskScoreBig"]),
        Spacer(1, 6),
        Table(
            [[Paragraph(label, styles["RiskLabel"])]],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(color)),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ])
        )
    ]

    right = [
        Paragraph("<b>Quick Snapshot</b>", styles["BodyBold"]),
        Spacer(1, 6),
        Paragraph(f"• <b>{failed_metrics}</b> of <b>{total_metrics}</b> fairness checks failed", styles["Body"]),
        Paragraph(f"• <b>{total_findings}</b> total bias findings detected", styles["Body"]),
        Paragraph("• Review recommendations before deployment", styles["Body"]),
    ]

    table = Table([[left, right]], colWidths=[180, 310])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# GENERIC INFO CARD
# ─────────────────────────────────────────────────────────────

def build_info_card(text, styles):
    table = Table([[Paragraph(str(text), styles["Body"])]], colWidths=[490])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# KPI TABLE
# ─────────────────────────────────────────────────────────────

def build_kpi_table(items, styles):
    row = []

    for label, value, color in items:
        cell = Table([
            [Paragraph(label, styles["Muted"])],
            [Paragraph(f"<font color='{color}'><b>{value}</b></font>", styles["BodyBold"])]
        ], colWidths=[110])

        cell.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        row.append(cell)

    table = Table([row], colWidths=[122, 122, 122, 122])
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return table


# ─────────────────────────────────────────────────────────────
# MODEL OVERVIEW CARD
# ─────────────────────────────────────────────────────────────

def build_model_overview_card(model_meta, styles):
    if not model_meta:
        return build_info_card("No model metadata available for overview.", styles)

    rows = [
        [
            Paragraph("<b>Model Type</b>", styles["BodyBold"]),
            Paragraph(str(model_meta.get("model_type", "-")), styles["Body"]),
            Paragraph("<b>Test Samples</b>", styles["BodyBold"]),
            Paragraph(str(model_meta.get("n_test_samples", "-")), styles["Body"]),
        ],
        [
            Paragraph("<b>Accuracy</b>", styles["BodyBold"]),
            Paragraph(format_number(model_meta.get("global_accuracy", 0), 4), styles["Body"]),
            Paragraph("<b>Precision</b>", styles["BodyBold"]),
            Paragraph(format_number(model_meta.get("global_precision", 0), 4), styles["Body"]),
        ],
        [
            Paragraph("<b>Recall</b>", styles["BodyBold"]),
            Paragraph(format_number(model_meta.get("global_recall", 0), 4), styles["Body"]),
            Paragraph("<b>F1 Score</b>", styles["BodyBold"]),
            Paragraph(format_number(model_meta.get("global_f1", 0), 4), styles["Body"]),
        ],
        [
            Paragraph("<b>Positive Label</b>", styles["BodyBold"]),
            Paragraph(str(model_meta.get("positive_label", "-")), styles["Body"]),
            Paragraph("<b>Sensitive Attributes</b>", styles["BodyBold"]),
            Paragraph(", ".join(model_meta.get("sensitive_attributes", [])) if isinstance(model_meta.get("sensitive_attributes", []), list) else "-", styles["Body"]),
        ]
    ]

    table = Table(rows, colWidths=[100, 145, 100, 145])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# LAYER SUMMARY TABLE
# ─────────────────────────────────────────────────────────────

def build_layer_summary_table(dataset_metrics, dataset_findings, model_metrics, model_findings, subgroup_performance, styles):
    data = [[
        Paragraph("<b>Layer</b>", styles["SmallCenter"]),
        Paragraph("<b>Metrics</b>", styles["SmallCenter"]),
        Paragraph("<b>Findings</b>", styles["SmallCenter"]),
        Paragraph("<b>Extras</b>", styles["SmallCenter"]),
    ]]

    data.append([
        Paragraph("Dataset Audit", styles["Body"]),
        Paragraph(str(len(dataset_metrics)), styles["BodyBold"]),
        Paragraph(str(len(dataset_findings)), styles["BodyBold"]),
        Paragraph("Distribution / label fairness", styles["Body"]),
    ])

    data.append([
        Paragraph("Model Audit", styles["Body"]),
        Paragraph(str(len(model_metrics)), styles["BodyBold"]),
        Paragraph(str(len(model_findings)), styles["BodyBold"]),
        Paragraph(f"{len(subgroup_performance)} subgroup profiles", styles["Body"]),
    ])

    table = Table(data, repeatRows=1, colWidths=[140, 90, 90, 170])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# TOP RISK DRIVERS
# ─────────────────────────────────────────────────────────────

def build_top_risk_drivers(metrics, findings, styles):
    failed = [m for m in metrics if not m.get("passed", False)]
    worst_metrics = sorted(failed, key=lambda x: safe_float(x.get("value", 0)), reverse=True)[:5]

    critical_findings = [f for f in findings if str(f.get("severity", "")).lower() in {"critical", "high"}][:5]

    text_parts = []

    if worst_metrics:
        text_parts.append("<b>Highest failing fairness metrics:</b><br/>")
        for m in worst_metrics:
            text_parts.append(
                f"• {m.get('sensitive_attribute', '-')} — {format_metric_name(m.get('metric_name', '-'))} "
                f"(value: {format_number(m.get('value', 0), 4)}, threshold: {format_number(m.get('threshold', 0), 4)})<br/>"
            )

    if critical_findings:
        text_parts.append("<br/><b>Most severe detected concerns:</b><br/>")
        for f in critical_findings:
            text_parts.append(f"• {f.get('description', 'No description')}<br/>")

    if not text_parts:
        return build_info_card("No major risk drivers identified.", styles)

    return build_info_card("".join(text_parts), styles)


# ─────────────────────────────────────────────────────────────
# METRICS TABLE
# ─────────────────────────────────────────────────────────────

def build_metrics_table(metrics, styles):
    if not metrics:
        return build_info_card("No fairness metrics available.", styles)

    data = [[
        Paragraph("<b>Attribute</b>", styles["SmallCenter"]),
        Paragraph("<b>Metric</b>", styles["SmallCenter"]),
        Paragraph("<b>Value</b>", styles["SmallCenter"]),
        Paragraph("<b>Threshold</b>", styles["SmallCenter"]),
        Paragraph("<b>Status</b>", styles["SmallCenter"]),
    ]]

    for m in metrics:
        passed = m.get("passed", False)
        status_text = "PASS" if passed else "FAIL"
        status_color = "#16A34A" if passed else "#DC2626"

        data.append([
            Paragraph(str(m.get("sensitive_attribute", "-")), styles["Body"]),
            Paragraph(format_metric_name(m.get("metric_name", "-")), styles["Body"]),
            Paragraph(format_number(m.get("value", 0), 4), styles["Body"]),
            Paragraph(format_number(m.get("threshold", 0), 4), styles["Body"]),
            Paragraph(f"<font color='{status_color}'><b>{status_text}</b></font>", styles["BodyBold"]),
        ])

    table = Table(data, repeatRows=1, colWidths=[85, 165, 75, 75, 80])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    return table


# ─────────────────────────────────────────────────────────────
# FINDING CARD
# ─────────────────────────────────────────────────────────────

def build_finding_card(idx, finding, styles):
    severity = str(finding.get("severity", "medium")).lower()
    severity_color = severity_to_hex(severity)

    title = f"{idx}. {format_metric_name(finding.get('finding_type', 'Finding'))}"
    attribute = finding.get("attribute", "-")
    description = finding.get("description", "No description available.")
    recommendation = finding.get("recommendation", "No recommendation provided.")
    source_layer = finding.get("source_layer", "model_audit")

    severity_badge = Table(
        [[Paragraph(severity.upper(), styles["RiskLabel"])]],
        colWidths=[60]
    )
    severity_badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(severity_color)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    content = [
        [Paragraph(f"<b>{title}</b>", styles["BodyBold"]), severity_badge],
        [Paragraph(f"<b>Layer:</b> {source_layer}", styles["Body"]), ""],
        [Paragraph(f"<b>Attribute:</b> {attribute}", styles["Body"]), ""],
        [Paragraph(f"<b>Description:</b> {description}", styles["Body"]), ""],
        [Paragraph(f"<b>Recommendation:</b> {recommendation}", styles["Body"]), ""],
    ]

    table = Table(content, colWidths=[420, 70])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("LINEBEFORE", (0, 0), (0, -1), 4, colors.HexColor(severity_color)),
        ("SPAN", (0, 1), (1, 1)),
        ("SPAN", (0, 2), (1, 2)),
        ("SPAN", (0, 3), (1, 3)),
        ("SPAN", (0, 4), (1, 4)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    return KeepTogether([table])


# ─────────────────────────────────────────────────────────────
# GROUP BREAKDOWN TABLE
# ─────────────────────────────────────────────────────────────

def build_group_breakdown_table(metrics, styles):
    rows = [[
        Paragraph("<b>Attribute</b>", styles["SmallCenter"]),
        Paragraph("<b>Group</b>", styles["SmallCenter"]),
        Paragraph("<b>Approval / Positive Rate</b>", styles["SmallCenter"]),
    ]]

    added = set()

    for m in metrics:
        attr = m.get("sensitive_attribute", "-")
        details = m.get("details", {})

        if not isinstance(details, dict):
            continue

        for group, value in details.items():
            if isinstance(value, dict):
                continue

            if str(group).lower() in {"alias_of", "tpr_diff", "fpr_diff"}:
                continue

            key = (attr, str(group))
            if key in added:
                continue
            added.add(key)

            try:
                pct = f"{float(value) * 100:.1f}%"
            except Exception:
                pct = str(value)

            rows.append([
                Paragraph(str(attr), styles["Body"]),
                Paragraph(str(group), styles["Body"]),
                Paragraph(pct, styles["BodyBold"]),
            ])

    if len(rows) == 1:
        return build_info_card("No group-level details available.", styles)

    table = Table(rows, repeatRows=1, colWidths=[110, 190, 190])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# SUBGROUP PERFORMANCE TABLE
# ─────────────────────────────────────────────────────────────

def build_subgroup_performance_table(subgroups, styles):
    if not subgroups:
        return build_info_card("No subgroup performance data available.", styles)

    rows = [[
        Paragraph("<b>Attribute</b>", styles["SmallCenter"]),
        Paragraph("<b>Group</b>", styles["SmallCenter"]),
        Paragraph("<b>N</b>", styles["SmallCenter"]),
        Paragraph("<b>Accuracy</b>", styles["SmallCenter"]),
        Paragraph("<b>Precision</b>", styles["SmallCenter"]),
        Paragraph("<b>Recall</b>", styles["SmallCenter"]),
        Paragraph("<b>F1</b>", styles["SmallCenter"]),
    ]]

    for s in subgroups:
        rows.append([
            Paragraph(str(s.get("sensitive_attribute", "-")), styles["Body"]),
            Paragraph(str(s.get("group", "-")), styles["Body"]),
            Paragraph(str(s.get("n_samples", 0)), styles["Body"]),
            Paragraph(format_number(s.get("accuracy", 0), 4), styles["Body"]),
            Paragraph(format_number(s.get("precision", 0), 4), styles["Body"]),
            Paragraph(format_number(s.get("recall", 0), 4), styles["Body"]),
            Paragraph(format_number(s.get("f1", 0), 4), styles["Body"]),
        ])

    table = Table(rows, repeatRows=1, colWidths=[90, 90, 45, 65, 65, 65, 70])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# SUBGROUP RISK TABLE
# ─────────────────────────────────────────────────────────────

def build_subgroup_risk_table(subgroups, styles):
    if not subgroups:
        return build_info_card("No subgroup risk data available.", styles)

    rows = [[
        Paragraph("<b>Attribute</b>", styles["SmallCenter"]),
        Paragraph("<b>Group</b>", styles["SmallCenter"]),
        Paragraph("<b>N</b>", styles["SmallCenter"]),
        Paragraph("<b>Recall</b>", styles["SmallCenter"]),
        Paragraph("<b>FNR</b>", styles["SmallCenter"]),
        Paragraph("<b>Risk Flag</b>", styles["SmallCenter"]),
    ]]

    for s in subgroups:
        fnr = safe_float(s.get("fnr", 0))
        n = int(s.get("n_samples", 0))

        if n < 15 or fnr > 0.20:
            flag = "<font color='#DC2626'><b>HIGH RISK</b></font>"
        elif n < 30 or fnr > 0.10:
            flag = "<font color='#D97706'><b>MEDIUM RISK</b></font>"
        else:
            flag = "<font color='#16A34A'><b>LOW RISK</b></font>"

        rows.append([
            Paragraph(str(s.get("sensitive_attribute", "-")), styles["Body"]),
            Paragraph(str(s.get("group", "-")), styles["Body"]),
            Paragraph(str(n), styles["Body"]),
            Paragraph(format_number(s.get("recall", 0), 4), styles["Body"]),
            Paragraph(format_number(fnr, 4), styles["Body"]),
            Paragraph(flag, styles["BodyBold"]),
        ])

    table = Table(rows, repeatRows=1, colWidths=[90, 95, 45, 75, 75, 110])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# MODEL META TABLE
# ─────────────────────────────────────────────────────────────

def build_model_meta_table(model_meta, styles):
    if not model_meta:
        return build_info_card("No model metadata available.", styles)

    rows = [[
        Paragraph("<b>Field</b>", styles["SmallCenter"]),
        Paragraph("<b>Value</b>", styles["SmallCenter"]),
    ]]

    fields = [
        ("Model Type", model_meta.get("model_type", "-")),
        ("Test Samples", model_meta.get("n_test_samples", "-")),
        ("Positive Label", model_meta.get("positive_label", "-")),
        ("Sensitive Attributes", ", ".join(model_meta.get("sensitive_attributes", [])) if isinstance(model_meta.get("sensitive_attributes", []), list) else "-"),
        ("Global Accuracy", format_number(model_meta.get("global_accuracy", 0), 4)),
        ("Global Precision", format_number(model_meta.get("global_precision", 0), 4)),
        ("Global Recall", format_number(model_meta.get("global_recall", 0), 4)),
        ("Global F1", format_number(model_meta.get("global_f1", 0), 4)),
    ]

    for label, value in fields:
        rows.append([
            Paragraph(str(label), styles["BodyBold"]),
            Paragraph(str(value), styles["Body"]),
        ])

    table = Table(rows, repeatRows=1, colWidths=[170, 320])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# PIPELINE META TABLE
# ─────────────────────────────────────────────────────────────

def build_pipeline_meta_table(pipeline_meta, styles):
    if not pipeline_meta:
        return build_info_card("No pipeline metadata available.", styles)

    rows = [[
        Paragraph("<b>Field</b>", styles["SmallCenter"]),
        Paragraph("<b>Value</b>", styles["SmallCenter"]),
    ]]

    for key, value in pipeline_meta.items():
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False)
        rows.append([
            Paragraph(format_metric_name(str(key)), styles["BodyBold"]),
            Paragraph(str(value), styles["Body"]),
        ])

    table = Table(rows, repeatRows=1, colWidths=[170, 320])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def section_title(text, styles):
    return Paragraph(text, styles["Section"])


def get_risk_label(score: float) -> str:
    if score >= 0.8:
        return "CRITICAL"
    elif score >= 0.6:
        return "HIGH"
    elif score >= 0.3:
        return "MEDIUM"
    return "LOW"


def get_risk_color(score: float) -> str:
    if score >= 0.8:
        return "#DC2626"
    elif score >= 0.6:
        return "#D97706"
    elif score >= 0.3:
        return "#CA8A04"
    return "#16A34A"


def get_deployment_status(score: float) -> str:
    if score >= 0.8:
        return "Do Not Deploy"
    elif score >= 0.6:
        return "Deploy With Remediation"
    elif score >= 0.3:
        return "Deploy With Monitoring"
    return "Deployable"


def get_deployment_color(score: float) -> str:
    if score >= 0.8:
        return "#DC2626"
    elif score >= 0.6:
        return "#D97706"
    elif score >= 0.3:
        return "#CA8A04"
    return "#16A34A"


def severity_to_hex(severity: str) -> str:
    return {
        "critical": "#DC2626",
        "high": "#D97706",
        "medium": "#CA8A04",
        "low": "#16A34A",
    }.get(severity, "#64748B")


def format_metric_name(name: str) -> str:
    return (name or "").replace("_", " ").title()


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_number(value, decimals=4):
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def ensure_list(value):
    return value if isinstance(value, list) else []


def normalize_subgroup_performance(items):
    if not isinstance(items, list):
        return []

    normalized = []

    for item in items:
        if not isinstance(item, dict):
            continue

        cm = item.get("confusion_matrix", {})
        if not isinstance(cm, dict):
            cm = {}

        normalized.append({
            "sensitive_attribute": str(item.get("sensitive_attribute", item.get("attribute", "Unknown"))),
            "group": str(item.get("group", "Unknown")),
            "n_samples": int(safe_float(item.get("n_samples", item.get("count", 0)), 0)),
            "accuracy": safe_float(item.get("accuracy", 0.0)),
            "precision": safe_float(item.get("precision", 0.0)),
            "recall": safe_float(item.get("recall", 0.0)),
            "f1": safe_float(item.get("f1", 0.0)),
            "fpr": safe_float(item.get("fpr", 0.0)),
            "fnr": safe_float(item.get("fnr", 0.0)),
            "confusion_matrix": {
                "tp": int(safe_float(cm.get("tp", 0), 0)),
                "fp": int(safe_float(cm.get("fp", 0), 0)),
                "tn": int(safe_float(cm.get("tn", 0), 0)),
                "fn": int(safe_float(cm.get("fn", 0), 0)),
            },
        })

    return normalized


def generate_model_interpretation(overall_risk, metrics, findings):
    failed = [m for m in metrics if not m.get("passed", False)]
    attrs = sorted(set(m.get("sensitive_attribute", "unknown") for m in failed))
    attr_text = ", ".join(attrs) if attrs else "no sensitive attributes"

    severe_findings = [f for f in findings if str(f.get("severity", "")).lower() in {"critical", "high"}]

    if overall_risk >= 0.8:
        risk_text = "This model presents <b>critical fairness risk</b> and shows strong evidence of subgroup disparity."
    elif overall_risk >= 0.6:
        risk_text = "This model presents <b>high fairness risk</b> and requires remediation before deployment."
    elif overall_risk >= 0.3:
        risk_text = "This model presents <b>moderate fairness risk</b> and should be monitored closely."
    else:
        risk_text = "This model presents <b>low fairness risk</b> based on the evaluated fairness criteria."

    explanation = (
        f"{risk_text}<br/><br/>"
        f"Failed fairness checks were observed across <b>{attr_text}</b>. "
        f"A total of <b>{len(failed)}</b> fairness metrics failed and "
        f"<b>{len(severe_findings)}</b> high-severity concerns were detected. "
        f"Special attention should be given to demographic parity, disparate impact, "
        f"equal opportunity, and false negative disparities where applicable."
    )

    return explanation


def generate_deployment_recommendation(overall_risk, findings):
    critical = len([f for f in findings if str(f.get("severity", "")).lower() == "critical"])
    high = len([f for f in findings if str(f.get("severity", "")).lower() == "high"])

    if overall_risk >= 0.8 or critical > 0:
        return (
            "<b>Recommendation:</b> <font color='#DC2626'><b>DO NOT DEPLOY</b></font><br/><br/>"
            "The current model exhibits critical fairness risk. Deployment is not recommended until "
            "subgroup disparities, data imbalance, and threshold fairness issues are remediated and re-audited."
        )

    if overall_risk >= 0.6 or high > 2:
        return (
            "<b>Recommendation:</b> <font color='#D97706'><b>DEPLOY ONLY AFTER REMEDIATION</b></font><br/><br/>"
            "The model should undergo mitigation steps such as rebalancing, threshold tuning, feature review, "
            "or fairness-aware retraining before production release."
        )

    if overall_risk >= 0.3:
        return (
            "<b>Recommendation:</b> <font color='#CA8A04'><b>DEPLOY WITH MONITORING</b></font><br/><br/>"
            "The model may be used with ongoing subgroup monitoring, drift detection, and periodic fairness revalidation."
        )

    return (
        "<b>Recommendation:</b> <font color='#16A34A'><b>DEPLOYABLE</b></font><br/><br/>"
        "The current audit does not indicate severe fairness concerns, though continuous monitoring is still recommended."
    )