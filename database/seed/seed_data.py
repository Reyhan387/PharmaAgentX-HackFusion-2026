import pandas as pd
from datetime import datetime
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.models import Patient, Medicine, Order
from backend.app.models.user import User
from backend.app.core.security import get_password_hash

# ===============================
# RESET DATABASE (Hackathon Safe)
# ===============================
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ===============================
# 1️⃣ LOAD MEDICINES
# ===============================

products_df = pd.read_excel("database/seed/products-export.xlsx")
products_df.columns = products_df.columns.str.strip()

for _, row in products_df.iterrows():
    medicine = Medicine(
        name=str(row["product name"]).strip(),
        price=float(row["price rec"]),
        stock=50,
        prescription_required=False
    )
    db.add(medicine)

db.commit()
print("✅ Medicines seeded")

# ===============================
# 2️⃣ LOAD PATIENTS + USERS
# ===============================

raw_df = pd.read_excel(
    "database/seed/Consumer Order History 1.xlsx",
    header=None
)

header_row = None
for i in range(len(raw_df)):
    if "Patient ID" in raw_df.iloc[i].values:
        header_row = i
        break

if header_row is None:
    raise Exception("❌ Could not find 'Patient ID' header")

history_df = pd.read_excel(
    "database/seed/Consumer Order History 1.xlsx",
    header=header_row
)

history_df.columns = history_df.columns.str.strip()
history_df = history_df.dropna(subset=["Patient ID"])

unique_patients = history_df[
    ["Patient ID", "Patient Age", "Patient Gender"]
].drop_duplicates()

patient_map = {}

for _, row in unique_patients.iterrows():

    external_id = str(row["Patient ID"]).strip()

    # Create User
    email = f"patient{external_id}@demo.com"

    user = User(
        email=email,
        hashed_password=get_password_hash("password123"),
        role="patient"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create Patient linked to User
    patient = Patient(
        external_patient_id=external_id,
        name=f"Patient {external_id}",
        age=int(row["Patient Age"]),
        gender=str(row["Patient Gender"]).strip(),
        user_id=user.id
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    patient_map[external_id] = patient.id

print("✅ Patients & Users seeded")

# ===============================
# HELPER: Convert Dosage
# ===============================

def parse_daily_dosage(dosage_string):
    try:
        dosage_string = dosage_string.lower()

        if "-" in dosage_string:
            parts = dosage_string.split("-")
            return sum(int(p) for p in parts if p.isdigit())

        if "per day" in dosage_string:
            return float(dosage_string.split()[0])

        return 1.0

    except:
        return 1.0

# ===============================
# INSERT ORDERS
# ===============================

for _, row in history_df.iterrows():

    external_id = str(row["Patient ID"]).strip()
    product_name = str(row["Product Name"]).strip()

    quantity = int(row["Quantity"])
    dosage_string = str(row["Dosage Frequency"]).strip()
    daily_dosage = parse_daily_dosage(dosage_string)

    purchase_date = row["Purchase Date"]
    if isinstance(purchase_date, pd.Timestamp):
        order_date = purchase_date.date()
    else:
        order_date = datetime.strptime(str(purchase_date), "%Y-%m-%d").date()

    medicine = db.query(Medicine).filter_by(name=product_name).first()

    if medicine and external_id in patient_map:

        order = Order(
            patient_id=patient_map[external_id],  # internal PK
            medicine_id=medicine.id,
            quantity=quantity,
            order_date=order_date,
            daily_dosage=daily_dosage,
            dosage_frequency=dosage_string
        )

        db.add(order)

db.commit()
db.close()

print("✅ Orders seeded")
print("🎉 FULL Data Seeding Completed Successfully")