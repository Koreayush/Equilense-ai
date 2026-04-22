from pydantic_settings import BaseSettings , SettingsConfigDict
from pydantic import ConfigDict

from functools import lru_cache
from typing import List 

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # App Settings
    APP_NAME: str = "EquiLens AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Audit Report Settings
    audit_report_dir: str = "storage/reports/dataset"
    model_report_dir: str = "storage/reports/model"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/unbiased_ai"

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  

    # Redis / Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # File Storage
    UPLOAD_DIR: str = "storage/uploads"
    REPORT_DIR: str = "storage/reports"
    MAX_UPLOAD_SIZE_MB: int = 50
    
    # Fairness Audit Thresholds
    DISPARATE_IMPACT_THRESHOLD : float = 0.8
    DEMOGRAPHIC_PARITY_WARNING_THRESHOLD : float = 0.1
    EQUAL_OPPORTUNITY_WARNING_THRESHOLD :float = 0.1 
    HIGH_RISK_THRESHOLD : float = 0.3 
    FAIRNESS_SCORE_MAX : int = 100
    
    
    # Supported use cases 
    SUPPORTED_USE_CASES : List[str] = ["hiring","Loan_approval","healthcare"]
    
    
    # Sensitive Attributes
    DEFAULT_SENSITIVE_COLUMNS : List[str] = [
        "gender",
        "sex",
        "race",
        "ethnicity",
        "age",
        "disability",
        "marital_status",
        "outcome"
    ]
    
    
    # Report Settings 
    DEFAULT_REPORT_FORMAT : str = "json"
    ENABLE_RECOMMENDATIONS : bool = True
    MAX_REPORT_FINDINGS : int = 20
    
    


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
