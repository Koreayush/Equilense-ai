from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from app.core.config import settings
from app.v1.endpoints import audit
from app.v1.endpoints import model_audit

# ─────────────────────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Fairness Auditing & Bias Detection API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# BASE PATHS
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "demo_output" / "hackathon-demo"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Reports directory mounted at: {REPORTS_DIR}")



# Mount reports as static downloadable files
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

# FRONTEND (STATIC UI)
FRONTEND_DIR = BASE_DIR / "app" / "static"

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")



# ─────────────────────────────────────────────────────────────
# API ROUTERS
# ─────────────────────────────────────────────────────────────
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Layer 1 - Dataset Audit"])
app.include_router(model_audit.router, prefix="/api/v1/model_audit", tags=["Layer 2 - Model Audit"])

# ─────────────────────────────────────────────────────────────
# HEALTH / ROOT ROUTES
# ─────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "reports_dir": str(REPORTS_DIR),
    }


from fastapi.responses import FileResponse
@app.get("/")
def serve_ui():
    return FileResponse(str(FRONTEND_DIR / "index.html"))