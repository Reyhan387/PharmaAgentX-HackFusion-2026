from datetime import datetime, timedelta
from sqlalchemy import func
from ..core.database import SessionLocal
from ..models.order import Order
from ..models.medicine import Medicine
from ..models.inventory_escalation import InventoryEscalation

# STEP 36 — Load Balancer Integration
from .load_balancer_service import enqueue_restock

PREDICTIVE_WINDOW_DAYS = 30
PREDICTIVE_DEPLETION_THRESHOLD_DAYS = 7
SAFETY_BUFFER_DAYS = 7
MINIMUM_RESTOCK_FLOOR = 40
HIGH_VELOCITY_THRESHOLD = 20  # Step 35 velocity threshold


# ==========================================================
# STEP 34 — Intelligent Dynamic Restock Quantity
# ==========================================================
def calculate_dynamic_restock_quantity(
    avg_daily_consumption: float,
    current_stock: int
) -> int:
    """
    Intelligent AI-based restock calculation.
    - Uses 30-day projection
    - Adds safety buffer
    - Enforces minimum floor
    - Rounded to nearest 10
    - Production-safe fallback
    """

    try:
        if avg_daily_consumption <= 0:
            return MINIMUM_RESTOCK_FLOOR

        projected_30_days = avg_daily_consumption * 30
        safety_buffer = avg_daily_consumption * SAFETY_BUFFER_DAYS
        target_stock = projected_30_days + safety_buffer

        restock_needed = target_stock - current_stock

        if restock_needed < MINIMUM_RESTOCK_FLOOR:
            restock_needed = MINIMUM_RESTOCK_FLOOR

        restock_needed = int(round(restock_needed / 10.0) * 10)

        return max(restock_needed, MINIMUM_RESTOCK_FLOOR)

    except Exception as e:
        print("Dynamic Restock Calculation Error:", e)
        return MINIMUM_RESTOCK_FLOOR


# ==========================================================
# STEP 35 — Restock Priority Intelligence Layer
# ==========================================================
def calculate_priority(
    days_until_depletion: float,
    avg_daily_consumption: float,
    current_stock: int,
    projected_30_day_demand: float,
    has_active_escalation: bool,
) -> str:
    """
    Deterministic priority scoring engine.
    No AI randomness.
    Production-safe.
    """

    score = 0

    # Depletion urgency
    if days_until_depletion <= 3:
        score += 50
    elif days_until_depletion <= 7:
        score += 30

    # Demand coverage
    if current_stock < (projected_30_day_demand * 0.5):
        score += 25

    # High velocity consumption
    if avg_daily_consumption > HIGH_VELOCITY_THRESHOLD:
        score += 15

    # Active escalation boost
    if has_active_escalation:
        score += 20

    if score >= 70:
        return "CRITICAL"
    elif score >= 40:
        return "WARNING"
    else:
        return "STABLE"


# ==========================================================
# STEP 33 + 34 + 35 + 36 — Predictive Demand Scan
# ==========================================================
def run_predictive_demand_scan():
    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow().date() - timedelta(days=PREDICTIVE_WINDOW_DAYS)

        medicines = db.query(Medicine).all()

        for medicine in medicines:

            total_quantity = (
                db.query(func.sum(Order.quantity))
                .filter(
                    Order.medicine_id == medicine.id,
                    Order.order_date >= cutoff_date
                )
                .scalar()
            )

            if total_quantity is None or total_quantity <= 0:
                continue

            avg_daily_consumption = total_quantity / PREDICTIVE_WINDOW_DAYS

            if avg_daily_consumption <= 0:
                continue

            current_stock = medicine.stock

            days_until_depletion = current_stock / avg_daily_consumption
            projected_30_day_demand = avg_daily_consumption * 30

            # ------------------------------------------------------
            # STEP 35 — Priority Evaluation
            # ------------------------------------------------------
            active_escalation = (
                db.query(InventoryEscalation)
                .filter(
                    InventoryEscalation.medicine_id == medicine.id,
                    InventoryEscalation.restock_triggered == False
                )
                .first()
            )

            priority = calculate_priority(
                days_until_depletion=days_until_depletion,
                avg_daily_consumption=avg_daily_consumption,
                current_stock=current_stock,
                projected_30_day_demand=projected_30_day_demand,
                has_active_escalation=bool(active_escalation),
            )

            print(
                f"[PRIORITY] Medicine={medicine.name} | "
                f"DaysLeft={round(days_until_depletion,2)} | "
                f"Priority={priority}"
            )

            # ------------------------------------------------------
            # Predictive Restock Trigger (NOW LOAD BALANCED)
            # ------------------------------------------------------
            if (
                days_until_depletion < PREDICTIVE_DEPLETION_THRESHOLD_DAYS
                or priority == "CRITICAL"
            ):

                print(
                    f"📊 Predictive alert: Medicine {medicine.id} "
                    f"may deplete in {round(days_until_depletion, 2)} days."
                )

                restock_quantity = calculate_dynamic_restock_quantity(
                    avg_daily_consumption=avg_daily_consumption,
                    current_stock=current_stock
                )

                if restock_quantity <= 0:
                    continue

                print(
                    f"[AI-RESTOCK] Medicine={medicine.name} | "
                    f"AvgDaily={round(avg_daily_consumption, 2)} | "
                    f"CurrentStock={current_stock} | "
                    f"RestockQuantity={restock_quantity} | "
                    f"Priority={priority}"
                )

                # ======================================================
                # STEP 36 — ENQUEUE INSTEAD OF DIRECT THREAD EXECUTION
                # ======================================================
                enqueue_restock(
                    medicine_id=medicine.id,
                    quantity=restock_quantity,
                    priority_level=priority
                )

    except Exception as e:
        print("Predictive Demand Scan Error:", e)

    finally:
        db.close()