from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import admin_required
from ..core.rbac import RBACService
from ..services.system_governor_service import update_mode

router = APIRouter(prefix="/admin/system", tags=["System Control"])


class ModeUpdate(BaseModel):
    mode: str


@router.post("/mode")
def change_system_mode(
    data: ModeUpdate,
    admin=Depends(admin_required),
    db: Session = Depends(get_db)
):
    RBACService.require_role(admin, ["admin"], db)

    config = update_mode(
        db=db,
        new_mode=data.mode,
        user_id=admin.id
    )

    return {"mode": config.current_mode}