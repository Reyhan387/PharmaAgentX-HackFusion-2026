from sqlalchemy.orm import Session
from datetime import datetime
from backend.app.models.system_config import SystemConfig

SAFE = "SAFE"
REVIEW = "REVIEW"
AUTO = "AUTO"


# ======================================
# Get Current System Mode
# ======================================

def get_current_mode(db: Session) -> str:
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()

    if not config:
        return SAFE  # Fail-safe default

    return config.current_mode


# ======================================
# Update Mode
# ======================================

def update_mode(db: Session, new_mode: str, user_id: int):
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()

    if not config:
        config = SystemConfig(
            id=1,
            current_mode=new_mode,
            updated_by=user_id,
            updated_at=datetime.utcnow()
        )
        db.add(config)
    else:
        config.current_mode = new_mode
        config.updated_by = user_id
        config.updated_at = datetime.utcnow()

    db.commit()
    return config


# ======================================
# Execution Governance Logic (STEP 43 FIX)
# ======================================

def is_execution_allowed(db: Session, risk_score: float, safe_threshold: float):
    mode = get_current_mode(db)

    # SAFE MODE → Hard Block
    if mode == SAFE:
        return False, "System in SAFE mode"

    # REVIEW MODE → Allow flow but prevent auto execution
    # Execution service will convert this into pending_review
    if mode == REVIEW:
        return True, "REVIEW_MODE_ACTIVE"

    # AUTO MODE → Risk-based execution
    if mode == AUTO:
        if risk_score >= safe_threshold:
            return True, "AUTO_MODE_ALLOWED"
        else:
            return False, "Risk below threshold"

    # Fallback safety
    return False, "Unknown mode fallback"