from pydantic import BaseModel
from typing import List, Optional


class DemographicsContext(BaseModel):
    patient_id: int
    age: Optional[int]
    gender: Optional[str]


class MedicalHistoryContext(BaseModel):
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    risk_score: Optional[float]


class OrderItem(BaseModel):
    order_id: int
    medicine_id: int
    quantity: int
    date: str
    status: str


class OrderContext(BaseModel):
    recent_orders: List[OrderItem]


class AIContext(BaseModel):
    demographics: DemographicsContext
    medical_history: MedicalHistoryContext
    orders: OrderContext