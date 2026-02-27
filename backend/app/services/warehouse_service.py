import requests
from backend.app.core.database import SessionLocal
from backend.app.models.inventory_escalation import InventoryEscalation

WAREHOUSE_URL = "http://127.0.0.1:8000/warehouse/fulfill"


def trigger_fulfillment(
    order_id: int = None,
    medicine_id: int = None,
    quantity: int = None  # ✅ NEW (optional, backward compatible)
):
    """
    Trigger warehouse automation.

    - If order_id → normal order fulfillment
    - If medicine_id → inventory restock request
    - If quantity provided → adaptive restock (Step 41)
    """

    # ----------------------------
    # ORDER FULFILLMENT (EXISTING)
    # ----------------------------
    if order_id:
        try:
            response = requests.post(
                WAREHOUSE_URL,
                params={"order_id": order_id},
                timeout=5
            )

            if response.status_code != 200:
                print(f"Warehouse returned non-200 status: {response.status_code}")

            return response.json()

        except Exception as e:
            print(f"Warehouse trigger failed: {e}")
            return {"error": str(e)}

    # ---------------------------------
    # INVENTORY RESTOCK (STEP 32 + 41)
    # ---------------------------------
    if medicine_id:
        db = SessionLocal()

        try:
            print(f"📦 Auto restock request for Medicine ID {medicine_id}")

            # Mark latest escalation as restock triggered
            escalation = (
                db.query(InventoryEscalation)
                .filter(InventoryEscalation.medicine_id == medicine_id)
                .order_by(InventoryEscalation.created_at.desc())
                .first()
            )

            if escalation:
                escalation.restock_triggered = True
                db.commit()

            # ----------------------------
            # Adaptive Quantity Support
            # ----------------------------
            params = {"medicine_id": medicine_id}

            if quantity and quantity > 0:
                params["quantity"] = quantity
                print(f"📈 Adaptive restock quantity applied: {quantity}")

            response = requests.post(
                WAREHOUSE_URL,
                params=params,
                timeout=5
            )

            if response.status_code != 200:
                print(f"Warehouse returned non-200 status: {response.status_code}")

            return response.json()

        except Exception as e:
            print(f"Restock trigger failed: {e}")
            return {"error": str(e)}

        finally:
            db.close()