import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float,
    ForeignKey, Integer, JSON, Text, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import enum



Base = declarative_base()


def gen_uuid():
    return str(uuid.uuid4())


class AuditStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Users

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner")


# Projects

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    use_case = Column(String , default="hiring")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    datasets = relationship("Dataset", back_populates="project")
    audit_runs = relationship("AuditRun", back_populates="project")


# Datasets 

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    row_count = Column(Integer)
    column_count = Column(Integer)
    target_column = Column(String)
    sensitive_columns = Column(JSON)
    prediction_column = Column(String)
    ground_truth_column = Column(String)   
    schema_meta = Column(JSON)        
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="datasets")
    audit_runs = relationship("AuditRun", back_populates="dataset")


# Audit Runs

class AuditRun(Base):
    __tablename__ = "audit_runs"

    id = Column(String, primary_key=True, default=gen_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    celery_task_id = Column(String)
    status = Column(Enum(AuditStatus), default=AuditStatus.PENDING)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="audit_runs")
    dataset = relationship("Dataset", back_populates="audit_runs")
    fairness_metrics = relationship("FairnessMetric", back_populates="audit_run")
    bias_findings = relationship("BiasFinding", back_populates="audit_run")
    report = relationship("Report", back_populates="audit_run", uselist=False)


# Fairness Metrics 

class FairnessMetric(Base):
    __tablename__ = "fairness_metrics"

    id = Column(String, primary_key=True, default=gen_uuid)
    audit_run_id = Column(String, ForeignKey("audit_runs.id"), nullable=False)
    sensitive_attribute = Column(String, nullable=False)  
    metric_name = Column(String, nullable=False)          
    value = Column(Float)
    threshold = Column(Float)
    passed = Column(Boolean)
    details = Column(JSON)

    audit_run = relationship("AuditRun", back_populates="fairness_metrics")



# severity 

class FindingSeverity(str , enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    

# Finding Type 

class FindingType(str , enum.Enum):
    REPRESENTATION = "representation"
    LABEL_IMBALANCE = "label_imbalance"
    MISSING = "missing"
    PREDICTION_DISPARITY = "prediction_disparity"
    PROXY_FEATURE = "proxy_feature"

#  Bias Findings

class BiasFinding(Base):
    __tablename__ = "bias_findings"

    id = Column(String, primary_key=True, default=gen_uuid)
    audit_run_id = Column(String, ForeignKey("audit_runs.id"), nullable=False)
    finding_type = Column(String)      
    finding_type = Column(Enum(FindingType))
    severity = Column(Enum(FindingSeverity))         
    attribute = Column(String)
    description = Column(Text)
    recommendation = Column(Text)
    raw_data = Column(JSON)

    audit_run = relationship("AuditRun", back_populates="bias_findings")


# Reports

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    audit_run_id = Column(String, ForeignKey("audit_runs.id"), nullable=False, unique=True)
    json_path = Column(String)
    pdf_path = Column(String)
    executive_summary = Column(Text)
    overall_risk_score = Column(Float)    
    generated_at = Column(DateTime, default=datetime.utcnow)

    audit_run = relationship("AuditRun", back_populates="report")
