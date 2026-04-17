"""
app/v1/endpoints/model_audit.py
================================
FastAPI endpoint for Layer 2: Model Fairness Inspection
and full merged fairness pipeline.

POST /api/v1/model-audit/run
GET  /api/v1/model-audit/status/{task_id}
"""

from __future__ import annotations

import os
import shutil
import tempfile
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from celery.result import AsyncResult

from app.workers.model_audit_worker import (
    celery_app,
    run_model_audit_task,
    run_full_model_pipeline_task,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_csv_list(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _coerce_positive_label(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


@router.post("/run")
async def run_model_audit(
    model_file: UploadFile = File(..., description="Trained model (.pkl or .joblib)"),
    csv_file: UploadFile = File(..., description="Test-set CSV"),
    target_column: str = Form(...),
    sensitive_columns: str = Form(..., description="Comma-separated list"),
    positive_label: str = Form("1"),
    feature_columns: str = Form("", description="Comma-separated; leave blank to auto-detect"),
    mode: str = Form("model_only", description="model_only or full_pipeline"),
    project_name: str = Form("Project"),
):
    """
    Queue a fairness audit task and return task metadata immediately.
    """
    audit_run_id = str(uuid.uuid4())
    upload_root = Path(tempfile.gettempdir()) / "unbiased_ai_uploads" / audit_run_id
    upload_root.mkdir(parents=True, exist_ok=True)

    try:
        if not model_file.filename:
            raise HTTPException(status_code=400, detail="Model file is required.")
        if not csv_file.filename:
            raise HTTPException(status_code=400, detail="CSV file is required.")

        model_path = upload_root / model_file.filename
        csv_path = upload_root / csv_file.filename

        with open(model_path, "wb") as fh:
            shutil.copyfileobj(model_file.file, fh)

        with open(csv_path, "wb") as fh:
            shutil.copyfileobj(csv_file.file, fh)

        sens_cols = _parse_csv_list(sensitive_columns)
        feat_cols = _parse_csv_list(feature_columns) or None
        pos_label = _coerce_positive_label(positive_label)

        if not sens_cols:
            raise HTTPException(
                status_code=422,
                detail="At least one sensitive column must be provided.",
            )

        if mode == "full_pipeline":
            task = run_full_model_pipeline_task.delay(
                audit_run_id=audit_run_id,
                model_path=str(model_path),
                dataset_path=str(csv_path),
                target_column=target_column,
                sensitive_columns=sens_cols,
                positive_label=pos_label,
                feature_columns=feat_cols,
                y_pred_column=None,
                project_name=project_name,
            )
        elif mode == "model_only":
            task = run_model_audit_task.delay(
                audit_run_id=audit_run_id,
                model_path=str(model_path),
                dataset_path=str(csv_path),
                target_column=target_column,
                sensitive_columns=sens_cols,
                positive_label=pos_label,
                feature_columns=feat_cols,
                project_name=project_name,
            )
        else:
            raise HTTPException(
                status_code=422,
                detail="Invalid mode. Use 'model_only' or 'full_pipeline'.",
            )

        return JSONResponse(
            status_code=202,
            content={
                "status": "queued",
                "audit_run_id": audit_run_id,
                "task_id": task.id,
                "mode": mode,
                "message": "Fairness audit has been queued successfully.",
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while queueing model audit")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")


@router.get("/status/{task_id}")
async def get_model_audit_status(task_id: str):
    """
    Poll task status from frontend.
    """
    try:
        task = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "state": task.state,
        }

        if task.state == "PENDING":
            response["status"] = "pending"

        elif task.state == "PROGRESS":
            response["status"] = "running"
            response["meta"] = task.info or {}

        elif task.state == "SUCCESS":
            response["status"] = "completed"
            response["result"] = task.result

        elif task.state == "FAILURE":
            response["status"] = "failed"
            response["error"] = str(task.info)

        else:
            response["status"] = task.state.lower()

        return JSONResponse(content=response)

    except Exception as exc:
        logger.exception("Failed to fetch model audit task status")
        raise HTTPException(status_code=500, detail=f"Internal error: {exc}")