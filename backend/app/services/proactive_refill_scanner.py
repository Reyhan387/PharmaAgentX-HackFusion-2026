from backend.app.core.database import SessionLocal
from backend.app.models.patient import Patient
from backend.app.models.refill_alert import RefillAlert
from backend.app.services.refill_predictor import predict_refills


def run_proactive_refill_scan():
    db = SessionLocal()

    try:
        patients = db.query(Patient).all()
        alerts_created = 0

        for patient in patients:

            predictions = predict_refills(db, patient.id)

            for item in predictions:
                if item["overdue"]:

                    existing_alert = db.query(RefillAlert).filter(
                        RefillAlert.patient_id == patient.id,
                        RefillAlert.medicine_name == item["medicine_name"],
                        RefillAlert.status == "pending"
                    ).first()

                    if not existing_alert:
                        alert = RefillAlert(
                            patient_id=patient.id,
                            medicine_name=item["medicine_name"],
                            expected_refill_date=item["expected_refill_date"],
                            status="pending"
                        )

                        db.add(alert)
                        alerts_created += 1

        db.commit()

        return {
            "message": "Proactive refill scan completed",
            "alerts_created": alerts_created
        }

    finally:
        db.close()