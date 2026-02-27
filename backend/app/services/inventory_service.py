from ..core.database import SessionLocal
from ..models.medicine import Medicine
from ..models.inventory_escalation import InventoryEscalation
from ..services.warehouse_service import trigger_fulfillment
from sqlalchemy import and_
from datetime import datetime
import threading

LOW_STOCK_THRESHOLD = 10  # Can later be moved to config


def inventory_threshold_scan():
    db = SessionLocal()

    try:
        medicines = db.query(Medicine).all()

        for med in medicines:

            # Safety check
            if med.stock is None:
                continue

            if med.stock < LOW_STOCK_THRESHOLD:

                # Prevent duplicate escalation for same stock level
                existing = db.query(InventoryEscalation).filter(
                    and_(
                        InventoryEscalation.medicine_id == med.id,
                        InventoryEscalation.current_stock == med.stock
                    )
                ).first()

                if existing:
                    continue

                escalation = InventoryEscalation(
                    medicine_id=med.id,
                    medicine_name=med.name,
                    current_stock=med.stock,
                    threshold=LOW_STOCK_THRESHOLD,
                    restock_triggered=False,
                    created_at=datetime.utcnow()
                )

                db.add(escalation)
                db.commit()

                print(f"⚠ Low stock detected for {med.name} (Stock: {med.stock})")

                # Non-blocking restock trigger
                threading.Thread(
                    target=_trigger_restock_signal,
                    args=(med.id,),
                    daemon=True
                ).start()

    except Exception as e:
        print("Inventory scan error:", str(e))

    finally:
        db.close()


def _trigger_restock_signal(medicine_id: int):
    try:
        trigger_fulfillment(medicine_id=medicine_id)
    except Exception as e:
        print("Restock signal failed:", str(e))