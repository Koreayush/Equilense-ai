"""
Celery Workers
==============
Background tasks so heavy audit jobs don't block the API.
"""

from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="run_audit")
def run_audit_task(
    self,
    audit_run_id: str,
    dataset_path: str,
    target_column: str,
    sensitive_columns: list[str],
    project_name: str = "Project",
):
    """
    Full async dataset audit pipeline:
      1. Load dataset from disk
      2. Run FairnessAuditEngine
      3. Generate PDF + JSON reports
      4. Return structured task result
    """

    import pandas as pd
    from app.services.audit.fairness_engine import FairnessAuditEngine
    from app.services.report.report_generator import generate_reports
    from app.core.config import settings

    self.update_state(state="PROGRESS", meta={"step": "loading_dataset"})
    df = pd.read_csv(dataset_path)

    self.update_state(state="PROGRESS", meta={"step": "running_audit"})
    engine = FairnessAuditEngine(df, target_column, sensitive_columns)
    result = engine.run()

    self.update_state(state="PROGRESS", meta={"step": "generating_reports"})
    json_path, pdf_path = generate_reports(
        result.to_dict(),
        output_dir=settings.REPORT_DIR,
        audit_run_id=audit_run_id,
        project_name=project_name,
    )

    return {
        "audit_run_id": audit_run_id,
        "task_type": "dataset_audit",
        "layer": "dataset",
        "status": "completed",
        "json_report": json_path,
        "pdf_report": pdf_path,
        "overall_risk_score": result.overall_risk_score,
        "executive_summary": result.executive_summary,
        "result": result.to_dict(),
    }