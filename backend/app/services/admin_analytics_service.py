from datetime import date
from sqlalchemy import func

from backend.app.core.database import SessionLocal
from backend.app.models import Patient, User, Medicine, Order


def get_admin_dashboard_stats():
    db = SessionLocal()

    try:
        total_patients = db.query(Patient).count()
        total_users = db.query(User).count()
        total_medicines = db.query(Medicine).count()
        total_orders = db.query(Order).count()

        # Orders this month
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)

        monthly_orders = db.query(Order).filter(
            Order.order_date >= first_day_of_month
        ).count()

        return {
            "total_users": total_users,
            "total_patients": total_patients,
            "total_medicines": total_medicines,
            "total_orders": total_orders,
            "orders_this_month": monthly_orders
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()