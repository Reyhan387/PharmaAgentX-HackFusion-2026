from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.services.admin_analytics_service import get_admin_dashboard_stats
from backend.app.services.proactive_refill_scanner import run_proactive_refill_scan
from backend.app.core.security import admin_required
from backend.app.core.database import SessionLocal, get_db
from backend.app.models.refill_alert import RefillAlert

# ✅ STEP 48 — Observability
from backend.app.services.observability_service import ObservabilityService
from backend.app.services.audit_service import create_audit_log

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==============================
# Existing Admin Dashboard
# ==============================

@router.get("/dashboard")
def admin_dashboard(user=Depends(admin_required)):
    return get_admin_dashboard_stats()


# ==============================
# Step 28 — Proactive Refill Scan
# ==============================

@router.post("/run-refill-scan")
def trigger_refill_scan(user=Depends(admin_required)):
    return run_proactive_refill_scan()


# ==============================
# View Refill Alerts
# ==============================

@router.get("/refill-alerts")
def get_refill_alerts(user=Depends(admin_required)):
    db = SessionLocal()

    try:
        alerts = db.query(RefillAlert).all()

        return [
            {
                "alert_id": alert.id,
                "patient_id": alert.patient_id,
                "medicine_name": alert.medicine_name,
                "expected_refill_date": alert.expected_refill_date,
                "status": alert.status,
                "created_at": alert.created_at
            }
            for alert in alerts
        ]

    finally:
        db.close()


# =====================================================
# STEP 48 — GET SYSTEM METRICS
# =====================================================

@router.get("/system-metrics")
def get_system_metrics(
    admin=Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Read-only system health metrics endpoint.
    Protected by admin authentication.
    Returns aggregated governance and observability metrics.
    """

    metrics = ObservabilityService.system_metrics(db)

    # Optional audit log for observability access tracking
    create_audit_log(
        db=db,
        event_type="OBSERVABILITY_CHECK",
        actor="admin",
        mode_at_time=metrics.get("current_mode", "UNKNOWN"),
        decision="metrics_viewed",
        risk_score=None,
        reference_id=None,
        reference_table=None,
    )

    return {
        "status": "ok",
        "metrics": metrics
    }