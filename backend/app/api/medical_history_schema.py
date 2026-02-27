from pydantic import BaseModel
from typing import List


class MedicalHistoryCreate(BaseModel):
    chronic_conditions: List[str]
    allergies: List[str]
    current_medications: List[str]