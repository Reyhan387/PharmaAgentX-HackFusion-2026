from fastapi import APIRouter
from ..services.mitigation_execution_service import execute_mitigation_if_safe

router = APIRouter(
    prefix="/mitigation-execute",
    tags=["Mitigation Execution"]
)


@router.post("/{medicine_id}")
def execute_safe_mitigation(medicine_id: int):
    """
    Controlled autonomous mitigation execution endpoint.
    Executes ONLY if safety rules pass.
    """
    return execute_mitigation_if_safe(medicine_id)