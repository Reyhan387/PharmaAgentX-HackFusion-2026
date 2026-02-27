from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..models.inventory_escalation import InventoryEscalation
from ..models.order import Order


LOOKBACK_DAYS = 14


def calculate_instability_multiplier(db: Session, medicine_id: int):
    """
    STEP 41 — Self-Healing Adaptive Intelligence

    Uses ONLY existing model fields.
    No schema change.
    Fully deterministic.
    """

    cutoff_datetime = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    cutoff_date = cutoff_datetime.date()

    # -------------------------------------------------
    # 1️⃣ Recent Escalations (uses created_at)
    # -------------------------------------------------
    recent_escalations = (
        db.query(InventoryEscalation)
        .filter(
            InventoryEscalation.medicine_id == medicine_id,
            InventoryEscalation.created_at >= cutoff_datetime
        )
        .count()
    )

    # -------------------------------------------------
    # 2️⃣ Recent Orders (uses order_date — FIXED)
    # -------------------------------------------------
    recent_orders = (
        db.query(Order)
        .filter(
            Order.medicine_id == medicine_id,
            Order.order_date >= cutoff_date
        )
        .count()
    )

    acceleration_flag = 1 if recent_orders >= 20 else 0

    # -------------------------------------------------
    # Instability Score
    # -------------------------------------------------
    instability_score = (
        recent_escalations * 25
        + acceleration_flag * 20
    )

    # -------------------------------------------------
    # Safe Multiplier Mapping
    # -------------------------------------------------
    if instability_score <= 30:
        multiplier = 1.0
    elif instability_score <= 60:
        multiplier = 1.15
    elif instability_score <= 90:
        multiplier = 1.30
    else:
        multiplier = 1.50

    return {
        "instability_score": instability_score,
        "multiplier": multiplier,
        "recent_escalations": recent_escalations,
        "recent_orders": recent_orders
    }