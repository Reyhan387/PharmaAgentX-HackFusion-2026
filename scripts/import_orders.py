import os
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.models.patient import Patient
from backend.app.models.medicine import Medicine
from backend.app.models.order import Order


# ✅ Exact file path
EXCEL_FILE_PATH = r"D:\Hackfusion\Website\1\pharmaagentx\database\seed\Consumer Order History 1.xlsx"


def import_orders():
    db: Session = SessionLocal()

    try:
        print("📂 Checking file path...")
        print("File exists:", os.path.exists(EXCEL_FILE_PATH))

        if not os.path.exists(EXCEL_FILE_PATH):
            print("❌ Excel file not found.")
            return

        print("📂 Reading Excel without header...")
        raw_df = pd.read_excel(EXCEL_FILE_PATH, header=None)

        # 🔍 Auto-detect header row
        header_row_index = None
        for i, row in raw_df.iterrows():
            if "Patient ID" in row.values:
                header_row_index = i
                break

        if header_row_index is None:
            print("❌ Could not find 'Patient ID' header row.")
            return

        print(f"✅ Header found at row index: {header_row_index}")

        # Re-read using correct header
        df = pd.read_excel(EXCEL_FILE_PATH, header=header_row_index)

        print("✅ Columns detected:", df.columns.tolist())

        for _, row in df.iterrows():

            if pd.isna(row.get("Patient ID")):
                continue

            # --------- Extract Data ---------
            external_id = str(row["Patient ID"]).strip()
            age = row.get("Patient Age")
            gender = row.get("Patient Gen") or row.get("Patient Gender")
            product_name = str(row["Product Name"]).strip()
            quantity = int(row["Quantity"])
            order_date = pd.to_datetime(row["Purchase Date"]).date()

            # --------- 1️⃣ Get or Create Patient ---------
            patient = db.query(Patient).filter(
                Patient.external_patient_id == external_id
            ).first()

            if not patient:
                patient = Patient(
                    external_patient_id=external_id,
                    name=external_id,
                    age=int(age) if not pd.isna(age) else None,
                    gender=str(gender) if gender else None
                )
                db.add(patient)
                db.commit()
                db.refresh(patient)
                print(f"👤 Created patient {external_id}")

            # --------- 2️⃣ Get or Create Medicine ---------
            medicine = db.query(Medicine).filter(
                Medicine.name == product_name
            ).first()

            if not medicine:
                medicine = Medicine(
                    name=product_name,
                    price=0.0,
                    stock=100,
                    prescription_required=False
                )
                db.add(medicine)
                db.commit()
                db.refresh(medicine)
                print(f"💊 Created medicine {product_name}")

            # --------- 3️⃣ Create Order ---------
            order = Order(
                patient_id=patient.id,
                medicine_id=medicine.id,
                quantity=quantity,
                order_date=order_date,
                daily_dosage=1,
                dosage_frequency="Once daily"
            )

            db.add(order)

        db.commit()
        print("🎉 Excel import completed successfully!")

    except Exception as e:
        print("❌ Error during import:", e)

    finally:
        db.close()


if __name__ == "__main__":
    import_orders()