# backend/app/core/rbac.py
# STEP 49 — Role-Based Access Control (RBAC) Hardening
# Deterministic access control enforcement with immutable denial logging.

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog


# =====================================================
# RBAC SERVICE — Deterministic Role Enforcement
# =====================================================

class RBACService:

    @staticmethod
    def require_role(user, allowed_roles: list, db: Session):
        """
        Checks if the user's role is in the allowed_roles list.
        If not, logs the denial immutably and raises 403.
        If allowed, returns immediately with zero overhead.

        Synchronous. Deterministic. Append-only logging.
        """

        if user.role in allowed_roles:
            return  # Access granted — no overhead

        # -----------------------------------------------
        # ACCESS DENIED — Log immutably, then raise 403
        # -----------------------------------------------
        denial_log = AuditLog(
            event_type="ACCESS_DENIED",
            actor=str(user.role),
            risk_score=None,
            mode_at_time="N/A",
            decision=f"Denied access to role {user.role}",
            reference_id=None,
            reference_table=None,
        )
        db.add(denial_log)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
