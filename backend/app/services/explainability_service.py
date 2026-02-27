from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.medicine import Medicine
from ..models.order import Order
from ..models.inventory_escalation import InventoryEscalation
from ..services.demand_service import (
    calculate_priority,
    calculate_dynamic_restock_quantity,
)

PREDICTIVE_WINDOW_DAYS = 30


# ==========================================================
# STEP 38 — Smart Adaptive Risk Engine
# ==========================================================
def compute_risk_score(
    days_until_depletion: float,
    projected_30_day_demand: float,
    escalation_active: bool,
    coverage_ratio: float,
    acceleration_factor: float,
    recent_escalation_count: int,
):
    score = 0

    # ------------------------------------------------------
    # 1️⃣ Depletion Urgency (existing logic preserved)
    # ------------------------------------------------------
    if days_until_depletion <= 3:
        score += 50
    elif days_until_depletion <= 7:
        score += 30
    elif days_until_depletion <= 14:
        score += 15

    # ------------------------------------------------------
    # 2️⃣ Absolute Demand Pressure (existing logic preserved)
    # ------------------------------------------------------
    if projected_30_day_demand > 100:
        score += 15
    elif projected_30_day_demand > 50:
        score += 10

    # ------------------------------------------------------
    # 3️⃣ Coverage Ratio Intelligence (NEW)
    # ------------------------------------------------------
    if coverage_ratio is not None:
        if coverage_ratio < 0.5:
            score += 30
        elif coverage_ratio < 1.0:
            score += 20
        elif coverage_ratio < 1.5:
            score += 10

    # ------------------------------------------------------
    # 4️⃣ Demand Acceleration Boost (NEW)
    # ------------------------------------------------------
    if acceleration_factor > 0.4:
        score += 25
    elif acceleration_factor > 0.2:
        score += 15

    # ------------------------------------------------------
    # 5️⃣ Active Escalation Boost (existing logic)
    # ------------------------------------------------------
    if escalation_active:
        score += 20

    # ------------------------------------------------------
    # 6️⃣ Repeated Escalation Boost (NEW)
    # ------------------------------------------------------
    if recent_escalation_count >= 4:
        score += 30
    elif recent_escalation_count >= 2:
        score += 15

    return min(score, 100)


def classify_risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    return "LOW"


def generate_explanation(
    days_until_depletion: float,
    projected_30_day_demand: float,
    escalation_active: bool,
    priority: str,
    coverage_ratio: float,
    acceleration_factor: float,
    recent_escalation_count: int,
):
    reasons = []

    reasons.append(
        f"Projected depletion in {round(days_until_depletion, 2)} days."
    )

    reasons.append(
        f"Projected 30-day demand: {round(projected_30_day_demand, 2)} units."
    )

    if coverage_ratio is not None:
        reasons.append(
            f"Stock coverage ratio: {round(coverage_ratio, 2)}."
        )

    if acceleration_factor > 0:
        reasons.append(
            f"Demand acceleration detected at {round(acceleration_factor * 100, 2)}% increase."
        )

    if escalation_active:
        reasons.append("Active inventory escalation detected.")

    if recent_escalation_count >= 2:
        reasons.append(
            f"{recent_escalation_count} escalations recorded in last 30 days."
        )

    reasons.append(f"Priority classified as {priority}.")

    return " ".join(reasons)


# ==========================================================
# STEP 38 — Main Smart-Adaptive Risk Snapshot
# ==========================================================
def get_medicine_risk_snapshot(db: Session, medicine_id: int):

    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        return {"error": "Medicine not found"}

    cutoff_date = datetime.utcnow().date() - timedelta(days=PREDICTIVE_WINDOW_DAYS)

    total_quantity = (
        db.query(func.sum(Order.quantity))
        .filter(
            Order.medicine_id == medicine.id,
            Order.order_date >= cutoff_date,
        )
        .scalar()
    )

    if not total_quantity or total_quantity <= 0:
        return {
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "risk_score": 0,
            "risk_level": "LOW",
            "explanation": "No recent consumption data available.",
        }

    avg_daily_consumption = total_quantity / PREDICTIVE_WINDOW_DAYS
    current_stock = medicine.stock

    if avg_daily_consumption <= 0:
        return {
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "risk_score": 0,
            "risk_level": "LOW",
            "explanation": "Consumption rate too low for calculation.",
        }

    # ------------------------------------------------------
    # Core Calculations
    # ------------------------------------------------------
    days_until_depletion = current_stock / avg_daily_consumption
    projected_30_day_demand = avg_daily_consumption * 30

    # Coverage Ratio
    coverage_ratio = None
    if projected_30_day_demand > 0:
        coverage_ratio = current_stock / projected_30_day_demand

    # ------------------------------------------------------
    # Demand Acceleration (last 7 vs previous 7 days)
    # ------------------------------------------------------
    now = datetime.utcnow().date()
    last_7 = now - timedelta(days=7)
    prev_7 = now - timedelta(days=14)

    recent_qty = (
        db.query(func.sum(Order.quantity))
        .filter(
            Order.medicine_id == medicine.id,
            Order.order_date >= last_7,
        )
        .scalar()
    ) or 0

    previous_qty = (
        db.query(func.sum(Order.quantity))
        .filter(
            Order.medicine_id == medicine.id,
            Order.order_date >= prev_7,
            Order.order_date < last_7,
        )
        .scalar()
    ) or 0

    acceleration_factor = 0
    if previous_qty > 0:
        acceleration_factor = (recent_qty - previous_qty) / previous_qty

    # ------------------------------------------------------
    # Escalation Intelligence
    # ------------------------------------------------------
    active_escalation = (
        db.query(InventoryEscalation)
        .filter(
            InventoryEscalation.medicine_id == medicine.id,
            InventoryEscalation.restock_triggered == False,
        )
        .first()
    )

    escalation_active = bool(active_escalation)

    escalation_cutoff = datetime.utcnow() - timedelta(days=30)

    recent_escalation_count = (
        db.query(InventoryEscalation)
        .filter(
            InventoryEscalation.medicine_id == medicine.id,
            InventoryEscalation.created_at >= escalation_cutoff,
        )
        .count()
    )

    # ------------------------------------------------------
    # Reuse Step 35 Priority Engine
    # ------------------------------------------------------
    priority = calculate_priority(
        days_until_depletion=days_until_depletion,
        avg_daily_consumption=avg_daily_consumption,
        current_stock=current_stock,
        projected_30_day_demand=projected_30_day_demand,
        has_active_escalation=escalation_active,
    )

    # ------------------------------------------------------
    # Adaptive Risk Score
    # ------------------------------------------------------
    risk_score = compute_risk_score(
        days_until_depletion=days_until_depletion,
        projected_30_day_demand=projected_30_day_demand,
        escalation_active=escalation_active,
        coverage_ratio=coverage_ratio,
        acceleration_factor=acceleration_factor,
        recent_escalation_count=recent_escalation_count,
    )

    risk_level = classify_risk_level(risk_score)

    recommended_restock = calculate_dynamic_restock_quantity(
        avg_daily_consumption=avg_daily_consumption,
        current_stock=current_stock,
    )

    explanation = generate_explanation(
        days_until_depletion=days_until_depletion,
        projected_30_day_demand=projected_30_day_demand,
        escalation_active=escalation_active,
        priority=priority,
        coverage_ratio=coverage_ratio,
        acceleration_factor=acceleration_factor,
        recent_escalation_count=recent_escalation_count,
    )

    return {
        "medicine_id": medicine.id,
        "medicine_name": medicine.name,
        "current_stock": current_stock,
        "avg_daily_consumption": round(avg_daily_consumption, 2),
        "days_until_depletion": round(days_until_depletion, 2),
        "projected_30_day_demand": round(projected_30_day_demand, 2),
        "coverage_ratio": round(coverage_ratio, 2) if coverage_ratio else None,
        "acceleration_factor": round(acceleration_factor, 3),
        "recent_escalation_count": recent_escalation_count,
        "priority": priority,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_restock_quantity": recommended_restock,
        "escalation_active": escalation_active,
        "explanation": explanation,
        "generated_at": datetime.utcnow(),
    }