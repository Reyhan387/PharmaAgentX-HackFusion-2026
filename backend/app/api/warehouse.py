from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.fulfillment_log import FulfillmentLog
from backend.app.models.medicine import Medicine

router = APIRouter(prefix="/warehouse", tags=["Warehouse"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/fulfill")
def fulfill_order(
    order_id: int = None,
    medicine_id: int = None,
    db: Session = Depends(get_db)
):

    # ===============================
    # ORDER FULFILLMENT (EXISTING)
    # ===============================
    if order_id:

        log = FulfillmentLog(
            order_id=order_id,
            status="PROCESSING",
            message="Order sent to warehouse for packing"
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return {
            "message": "Warehouse processing started",
            "order_id": order_id
        }

    # ===============================
    # INVENTORY RESTOCK (NEW SUPPORT)
    # ===============================
    if medicine_id:

        medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()

        if not medicine:
            raise HTTPException(status_code=404, detail="Medicine not found")

        # Simulate restock (add 50 units)
        medicine.stock += 50

        log = FulfillmentLog(
            order_id=None,
            status="RESTOCK",
            message=f"Auto restock completed for Medicine ID {medicine_id}"
        )

        db.add(log)
        db.commit()
        db.refresh(log)

        return {
            "message": "Medicine restocked successfully",
            "medicine_id": medicine_id,
            "new_stock": medicine.stock
        }

    # ===============================
    # INVALID REQUEST
    # ===============================
    raise HTTPException(status_code=400, detail="order_id or medicine_id required")