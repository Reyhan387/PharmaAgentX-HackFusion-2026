from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    event_type: str,
    actor: str,
    mode_at_time: str,
    decision: str,
    risk_score: int = None,
    reference_id: int = None,
    reference_table: str = None
):
    """
    Structured immutable audit logger.
    Append-only. No update. No delete.
    """

    log = AuditLog(
        event_type=event_type,
        actor=actor,
        risk_score=risk_score,
        mode_at_time=mode_at_time,
        decision=decision,
        reference_id=reference_id,
        reference_table=reference_table,
    )

    db.add(log)
    db.commit()