from fastapi import FastAPI
from dotenv import load_dotenv
import os

# ===============================
# Load Environment Variables
# ===============================

load_dotenv()

# ===============================
# Database Setup
# ===============================

from backend.app.core.database import engine, Base
import backend.app.models  # Ensures all models are registered

# ===============================
# Import Scheduler (STEP 31)
# ===============================

from backend.app.core.scheduler import start_scheduler, shutdown_scheduler

# ===============================
# Import API Routers
# ===============================

from backend.app.api import refill
from backend.app.api import patient_dashboard
from backend.app.api import admin_analytics
from backend.app.api import auth
from backend.app.api import medical_history_routes
from backend.app.api import ai_context
from backend.app.api import agent_routes
from backend.app.api import warehouse

# ✅ STEP 37 — Explainability Router
from backend.app.api import explainability

# ✅ STEP 39 — Mitigation Router
from backend.app.api import mitigation

# ✅ STEP 40 — Controlled Mitigation Execution Router
from backend.app.api import mitigation_execution

# ✅ STEP 42 — System Mode Control Router (NEW)
from backend.app.api import system_mode

# ✅ STEP 43 — Human Approval Router
from backend.app.api import admin_mitigation


# ===============================
# Create FastAPI App
# ===============================

app = FastAPI(
    title="PharmaAgentX",
    version="2.5.0",  # Version bump for System Control
    description="Agentic AI-powered Pharmacy Backend with Risk, Mitigation, Controlled Execution, Governance & Human Approval Workflow"
)

# ===============================
# Register Routers
# ===============================

app.include_router(refill.router)
app.include_router(patient_dashboard.router)
app.include_router(admin_analytics.router)
app.include_router(auth.router)
app.include_router(medical_history_routes.router)
app.include_router(ai_context.router)
app.include_router(agent_routes.router)
app.include_router(warehouse.router)

# ✅ STEP 37
app.include_router(explainability.router, prefix="/explain", tags=["Explainability"])

# ✅ STEP 39
app.include_router(mitigation.router, prefix="/mitigation", tags=["Mitigation"])

# ✅ STEP 40
app.include_router(
    mitigation_execution.router,
    prefix="/mitigation-execute",
    tags=["Mitigation Execution"]
)

# ✅ STEP 42 (NEW)
app.include_router(system_mode.router)

# ✅ STEP 43
app.include_router(admin_mitigation.router)

# ===============================
# Create Database Tables
# ===============================

Base.metadata.create_all(bind=engine)

# ===============================
# Scheduler Startup / Shutdown
# ===============================

@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()


# ===============================
# Root Endpoint
# ===============================

@app.get("/")
def root():
    return {
        "message": "PharmaAgentX Agentic Backend Running",
        "llm_provider": os.getenv("LLM_PROVIDER"),
        "system_version": "2.5.0",
        "risk_intelligence": "enabled",
        "mitigation_engine": "enabled",
        "controlled_autonomous_execution": "enabled",
        "human_approval_workflow": "enabled",
        "governance_mode_control": "enabled",  # ✅ NEW
        "status": "healthy"
    }