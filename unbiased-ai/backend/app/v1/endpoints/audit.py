from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import pandas as pd
import io
import os
import logging
from pathlib import Path

from app.services.audit.fairness_engine import FairnessAuditEngine
from app.services.report.report_generator import generate_reports

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Reports Folder Setup ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[3]   # backend/
REPORT_DIR = BASE_DIR / "demo_output" / "hackathon-demo"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/run")
async def run_audit(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    sensitive_columns: str = Form(...),
    y_pred_column: str | None = Form(None),
    positive_label: str = Form("1"),
):
    """
    Run fairness audit on uploaded CSV dataset and generate downloadable reports.
    """

    # ── Validate file ───────────────────────────────────────────────────────
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        logger.exception("CSV read failed")
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")

    # ── Parse sensitive columns ─────────────────────────────────────────────
    sensitive_cols = [col.strip() for col in sensitive_columns.split(",") if col.strip()]

    if not sensitive_cols:
        raise HTTPException(status_code=400, detail="At least one sensitive column is required.")

    # ── Validate required columns ───────────────────────────────────────────
    missing_columns = [col for col in [target_column, *sensitive_cols] if col not in df.columns]
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns in CSV: {missing_columns}"
        )

    if y_pred_column and y_pred_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"Prediction column '{y_pred_column}' not found in CSV."
        )

    # ── Parse positive label ────────────────────────────────────────────────
    try:
        positive_label_parsed = int(positive_label)
    except ValueError:
        positive_label_parsed = positive_label

    try:
        logger.info("Starting fairness audit...")
        logger.info(f"Target column: {target_column}")
        logger.info(f"Sensitive columns: {sensitive_cols}")
        logger.info(f"Prediction column: {y_pred_column}")
        logger.info(f"Positive label: {positive_label_parsed}")

        # ── Run audit engine ────────────────────────────────────────────────
        engine = FairnessAuditEngine(
            df=df,
            target_column=target_column,
            sensitive_columns=sensitive_cols,
            positive_label=positive_label_parsed,
            y_pred_column=y_pred_column,
        )

        result = engine.run()
        result_dict = result.to_dict()

        # ── Generate reports ────────────────────────────────────────────────
        json_path, pdf_path = generate_reports(
            result_dict,
            output_dir=str(REPORT_DIR),
            audit_run_id="hackathon-demo",
            project_name="AI Fairness Audit Report",
        )

        logger.info(f"Reports generated successfully: {json_path}, {pdf_path}")

        # ── Add report URLs for frontend ────────────────────────────────────
        result_dict["report_urls"] = {
            "pdf": "/reports/report.pdf",
            "json": "/reports/report.json"
        }

        return result_dict

    except Exception as e:
        logger.exception("Audit execution failed")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")