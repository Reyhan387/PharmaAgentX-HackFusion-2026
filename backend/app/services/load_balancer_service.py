import threading
from queue import PriorityQueue
from datetime import datetime

# ✅ Use your existing fulfillment function
from .warehouse_service import trigger_fulfillment


# ==============================
# Simulated Operational Capacity
# ==============================

MAX_CRITICAL_CONCURRENT = 2
MAX_WARNING_QUEUE = 4

critical_semaphore = threading.Semaphore(MAX_CRITICAL_CONCURRENT)

# Lower number = higher priority
restock_queue = PriorityQueue()

PRIORITY_MAP = {
    "CRITICAL": 1,
    "WARNING": 2,
    "STABLE": 3
}


# ==============================
# Enqueue Restock
# ==============================
def enqueue_restock(medicine_id, quantity, priority_level):
    """
    Adds restock task to intelligent load-controlled queue
    """
    priority_score = PRIORITY_MAP.get(priority_level, 3)
    timestamp = datetime.utcnow().timestamp()

    # FIFO maintained for same priority
    restock_queue.put((priority_score, timestamp, medicine_id, quantity))


# ==============================
# Scheduler-Driven Processor
# ==============================
def process_restock_queue():
    """
    Dispatch restocks intelligently based on capacity constraints.
    """
    while not restock_queue.empty():
        priority_score, _, medicine_id, quantity = restock_queue.get()

        if priority_score == 1:  # CRITICAL
            critical_semaphore.acquire()

            threading.Thread(
                target=_execute_and_release,
                kwargs={
                    "medicine_id": medicine_id,
                    "quantity": quantity
                },
                daemon=True
            ).start()

        elif priority_score == 2:  # WARNING
            if restock_queue.qsize() <= MAX_WARNING_QUEUE:
                threading.Thread(
                    target=trigger_fulfillment,
                    kwargs={
                        "medicine_id": medicine_id,
                        "quantity": quantity
                    },
                    daemon=True
                ).start()

        else:  # STABLE
            threading.Thread(
                target=trigger_fulfillment,
                kwargs={
                    "medicine_id": medicine_id,
                    "quantity": quantity
                },
                daemon=True
            ).start()


def _execute_and_release(medicine_id, quantity):
    try:
        trigger_fulfillment(
            medicine_id=medicine_id,
            quantity=quantity
        )
    finally:
        critical_semaphore.release()