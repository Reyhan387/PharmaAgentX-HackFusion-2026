from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import admin_required
from ..core.rbac import RBACService
from ..services.mitigation_execution_service import execute_mitigation_if_safe

router = APIRouter(
    prefix="/mitigation-execute",
    tags=["Mitigation Execution"]
)


@router.post("/{medicine_id}")
def execute_safe_mitigation(
    medicine_id: int,
    admin=Depends(admin_required),
    db: Session = Depends(get_db)
):
    """
    Controlled autonomous mitigation execution endpoint.
    Executes ONLY if safety rules pass.
    """
    RBACService.require_role(admin, ["admin", "system"], db)
    return execute_mitigation_if_safe(medicine_id)