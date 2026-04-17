from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.model_inspection.pipeline import run_model_audit_pipeline
import tempfile
import shutil
import os
import pandas as pd

router = APIRouter()

ALLOWED_MODEL_EXTENSIONS = {".pkl", ".joblib", ".onnx"}
ALLOWED_EVAL_EXTENSION = ".csv"


@router.post("/run")
async def run_model_audit(
    model_file: UploadFile = File(...),
    eval_file: UploadFile = File(...),
    target_column: str = Form(...),
    sensitive_columns: str = Form(...),
    y_pred_column: str = Form(""),
    positive_label: str = Form("1"),
):
    if not model_file.filename:
        raise HTTPException(status_code=400, detail="Model file is required.")

    if not eval_file.filename:
        raise HTTPException(status_code=400, detail="Evaluation dataset is required.")

    model_ext = os.path.splitext(model_file.filename)[1].lower()
    eval_ext = os.path.splitext(eval_file.filename)[1].lower()

    if model_ext not in ALLOWED_MODEL_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported model file type. Allowed: .pkl, .joblib, .onnx"
        )

    if eval_ext != ALLOWED_EVAL_EXTENSION:
        raise HTTPException(
            status_code=400,
            detail="Evaluation dataset must be a CSV."
        )

    sensitive_cols = [c.strip() for c in sensitive_columns.split(",") if c.strip()]
    if not sensitive_cols:
        raise HTTPException(
            status_code=400,
            detail="At least one sensitive column is required."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, model_file.filename)
        eval_path = os.path.join(tmpdir, eval_file.filename)

        with open(model_path, "wb") as f:
            shutil.copyfileobj(model_file.file, f)

        with open(eval_path, "wb") as f:
            shutil.copyfileobj(eval_file.file, f)

        df = pd.read_csv(eval_path)

        if target_column not in df.columns:
            raise HTTPException(
                status_code=400,
                detail=f"Target column '{target_column}' not found in evaluation CSV."
            )

        for col in sensitive_cols:
            if col not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Sensitive column '{col}' not found in evaluation CSV."
                )

        result = run_model_audit_pipeline(
            model_path=model_path,
            eval_csv_path=eval_path,
            target_column=target_column,
            sensitive_columns=sensitive_cols,
            positive_label=positive_label,
        )

        result["positive_label"] = positive_label
        result["y_pred_column"] = y_pred_column
        result["n_test_samples"] = len(df)
        result["model_filename"] = model_file.filename
        result["eval_filename"] = eval_file.filename

        return result