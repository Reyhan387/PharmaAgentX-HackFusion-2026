from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

from ..services.refill_service import scan_and_create_refill_alerts
from ..services.inventory_service import inventory_threshold_scan
from ..services.demand_service import run_predictive_demand_scan
from ..services.mitigation_execution_service import execute_mitigation_if_safe
from ..core.database import SessionLocal
from ..models.medicine import Medicine


# ===============================
# Logging Configuration
# ===============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("pharmaagentx.scheduler")

scheduler = BackgroundScheduler()
_scheduler_started = False  # Prevent duplicate starts


# ==========================================
# REFILL SCAN JOB
# ==========================================

def refill_scan_job():
    db = SessionLocal()
    try:
        logger.info("🔁 Running scheduled refill scan...")
        scan_and_create_refill_alerts(db)
        logger.info("✅ Refill scan completed successfully.")
    except Exception as e:
        logger.error(f"❌ Refill scan failed: {str(e)}")
    finally:
        db.close()


# ==========================================
# INVENTORY THRESHOLD JOB
# ==========================================

def inventory_scan_job():
    try:
        logger.info("📦 Running scheduled inventory threshold scan...")
        inventory_threshold_scan()
        logger.info("✅ Inventory scan completed successfully.")
    except Exception as e:
        logger.error(f"❌ Inventory scan failed: {str(e)}")


# ==========================================
# PREDICTIVE DEMAND JOB
# ==========================================

def predictive_demand_job():
    try:
        logger.info("📊 Running predictive demand intelligence scan...")
        run_predictive_demand_scan()
        logger.info("✅ Predictive demand scan completed successfully.")
    except Exception as e:
        logger.error(f"❌ Predictive demand scan failed: {str(e)}")


# ==========================================
# AUTONOMOUS MITIGATION EXECUTION JOB (STEP 40C)
# ==========================================

def autonomous_mitigation_job():
    db = SessionLocal()
    try:
        logger.info("🧠 Running autonomous mitigation execution scan...")

        medicines = db.query(Medicine).all()

        for medicine in medicines:
            result = execute_mitigation_if_safe(medicine.id)

            if result and result.get("status") == "executed":
                logger.info(
                    f"🚀 Autonomous mitigation executed for Medicine ID {medicine.id}"
                )

        logger.info("✅ Autonomous mitigation scan completed.")

    except Exception as e:
        logger.error(f"❌ Autonomous mitigation scan failed: {str(e)}")
    finally:
        db.close()


# ==========================================
# START SCHEDULER
# ==========================================

def start_scheduler():
    global _scheduler_started

    if _scheduler_started:
        logger.info("⚠ Scheduler already running. Skipping duplicate start.")
        return

    logger.info("🧠 Registering scheduled jobs...")

    scheduler.add_job(
        refill_scan_job,
        trigger=IntervalTrigger(minutes=5),
        id="refill_scan_job",
        replace_existing=True,
    )

    scheduler.add_job(
        inventory_scan_job,
        trigger=IntervalTrigger(minutes=3),
        id="inventory_scan_job",
        replace_existing=True,
    )

    scheduler.add_job(
        predictive_demand_job,
        trigger=IntervalTrigger(minutes=10),
        id="predictive_demand_job",
        replace_existing=True,
    )

    scheduler.add_job(
        autonomous_mitigation_job,
        trigger=IntervalTrigger(minutes=4),
        id="autonomous_mitigation_job",
        replace_existing=True,
    )

    scheduler.start()
    _scheduler_started = True

    # Log all registered jobs
    for job in scheduler.get_jobs():
        logger.info(f"🗂 Registered Job: {job.id}")

    logger.info("🚀 APScheduler started with full autonomous intelligence.")


# ==========================================
# SHUTDOWN
# ==========================================

def shutdown_scheduler():
    global _scheduler_started

    if scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 APScheduler stopped.")

    _scheduler_started = False