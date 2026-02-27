from fastapi import APIRouter, Depends
from backend.app.services.admin_analytics_service import get_admin_dashboard_stats
from backend.app.services.proactive_refill_scanner import run_proactive_refill_scan
from backend.app.core.security import admin_required
from backend.app.core.database import SessionLocal
from backend.app.models.refill_alert import RefillAlert

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