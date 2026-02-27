from langchain.tools import StructuredTool
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Session
import threading

from ..core.database import SessionLocal
from ..models.medicine import Medicine
from ..models.order import Order
from ..services.refill_predictor import predict_refills
from ..services.warehouse_service import trigger_fulfillment


# =====================================================
# 1️⃣ CHECK INVENTORY TOOL
# =====================================================

class InventoryInput(BaseModel):
    medicine_name: str


def check_inventory(medicine_name: str) -> str:
    db: Session = SessionLocal()
    try:
        med = db.query(Medicine).filter(
            Medicine.name.ilike(f"%{medicine_name}%")
        ).first()

        if not med:
            return "Medicine not found."

        if med.stock > 0:
            return f"{med.name} is in stock. Quantity available: {med.stock}"
        else:
            return f"{med.name} is currently out of stock."

    finally:
        db.close()


check_inventory_tool = StructuredTool.from_function(
    func=check_inventory,
    name="check_inventory",
    description=(
        "Check if a medicine is available in inventory. "
        "You must pass JSON input with key: medicine_name (string)."
    ),
    args_schema=InventoryInput,
)


# =====================================================
# 2️⃣ CREATE ORDER TOOL (STEP 30 – THREAD SAFE)
# =====================================================

class CreateOrderInput(BaseModel):
    patient_id: int
    medicine_name: str
    quantity: int


def create_order(patient_id: int, medicine_name: str, quantity: int) -> str:
    db: Session = SessionLocal()
    try:
        med = db.query(Medicine).filter(
            Medicine.name.ilike(f"%{medicine_name}%")
        ).first()

        if not med:
            return "Medicine not found."

        if med.stock < quantity:
            return "Insufficient stock."

        order = Order(
            patient_id=patient_id,
            medicine_id=med.id,
            quantity=quantity,
            order_date=datetime.utcnow(),
            daily_dosage=1
        )

        # Reduce inventory
        med.stock -= quantity

        db.add(order)
        db.commit()
        db.refresh(order)

        # =================================================
        # 🔥 STEP 30 – NON-BLOCKING BACKGROUND THREAD
        # =================================================
        threading.Thread(
            target=trigger_fulfillment,
            args=(order.id,),
            daemon=True
        ).start()

        return (
            f"Order successfully created for {quantity} units of {med.name}. "
            f"Order ID: {order.id}"
        )

    except Exception as e:
        db.rollback()
        return f"Order creation failed: {str(e)}"

    finally:
        db.close()


create_order_tool = StructuredTool.from_function(
    func=create_order,
    name="create_order",
    description=(
        "Create a medicine order for a patient. "
        "You MUST provide JSON input with keys: "
        "patient_id (integer), medicine_name (string), quantity (integer). "
        "Never pass comma-separated strings."
    ),
    args_schema=CreateOrderInput,
)


# =====================================================
# 3️⃣ PROACTIVE REFILL TOOL
# =====================================================

class RefillInput(BaseModel):
    patient_id: int


def proactive_refill_check(patient_id: int) -> str:
    db: Session = SessionLocal()
    try:
        predictions = predict_refills(db, patient_id)

        if not predictions:
            return "No refill data found for this patient."

        urgent = []

        for p in predictions:
            if p["overdue"] or p["days_remaining"] <= 3:
                status = "OVERDUE" if p["overdue"] else "DUE SOON"
                urgent.append(
                    f"{p['medicine_name']} → {status} "
                    f"(Expected refill: {p['expected_refill_date']})"
                )

        if not urgent:
            return "No refills needed at the moment."

        return " | ".join(urgent)

    finally:
        db.close()


proactive_refill_tool = StructuredTool.from_function(
    func=proactive_refill_check,
    name="proactive_refill_check",
    description=(
        "Check refill urgency for a patient. "
        "You must pass JSON input with key: patient_id (integer)."
    ),
    args_schema=RefillInput,
)