import json

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    actor: str,
    action: str,
    entity_type=None,
    entity_id=None,
    details=None,
):
    if isinstance(details, dict):
        details = json.dumps(
            details,
            ensure_ascii=False
        )

    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id)
        if entity_id is not None
        else None,
        details=details,
    )

    db.add(entry)
    db.commit()

    return entry
