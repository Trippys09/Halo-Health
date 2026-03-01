"""
HALO Health – FastAPI Application Entrypoint
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Disable ChromaDB Telemetry globally to prevent ClientStartEvent bugs
os.environ["ANONYMIZED_TELEMETRY"] = "False"

from backend.database import create_tables
from backend.routers import (
    auth,
    sessions,
    wellbeing,
    insurance,
    diagnostic,
    virtual_doctor,
    dietary,
    orchestrator,
    visualisation,
    audit,
    oculomics,
)
from backend.routers.share import share_router
from backend.routers.audit import log_event

app = FastAPI(
    title="HALO Health API",
    description="Multi-Agent AI Healthcare Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    create_tables()
    # Log startup and selected models
    try:
        from backend.services.model_selector import get_pro_model, get_flash_model
        pro = get_pro_model()
        flash = get_flash_model()
        log_event("INFO", "startup", "HALO Health API started",
                  f"Pro model: {pro} | Flash model: {flash}")
    except Exception as exc:
        log_event("WARNING", "startup", "API started (model detection failed)", str(exc))


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "HALO Health API"}


# ── Mount Routers ─────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(wellbeing.router)
app.include_router(insurance.router)
app.include_router(diagnostic.router)
app.include_router(virtual_doctor.router)
app.include_router(dietary.router)
app.include_router(orchestrator.router)
app.include_router(visualisation.router)
app.include_router(audit.router)
app.include_router(oculomics.router)
app.include_router(share_router)

# Serve GradCAM output dir for frontend rendering
GRADCAM_DIR = os.path.join(os.path.dirname(__file__), "oculomics", "artifacts", "gradcam_inference")
try:
    os.makedirs(GRADCAM_DIR, exist_ok=True)
except (OSError, PermissionError):
    import tempfile
    GRADCAM_DIR = os.path.join(tempfile.gettempdir(), "medora_gradcam")
    os.makedirs(GRADCAM_DIR, exist_ok=True)

app.mount("/gradcam", StaticFiles(directory=GRADCAM_DIR), name="gradcam")
