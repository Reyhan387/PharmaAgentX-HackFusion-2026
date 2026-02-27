from fastapi import BackgroundTasks
from app.services.fulfillment_service import trigger_fulfillment

def dispatch_event(event_name: str, payload: dict, background_tasks: BackgroundTasks):
    
    if event_name == "ORDER_CREATED":
        background_tasks.add_task(
            trigger_fulfillment,
            payload["order_id"]
        )