"""Journalisation d'audit (CdC Module 8) — append-only, jamais de commit ici :
la trace rejoint la transaction de l'action auditée (tout ou rien : une action
sans sa trace ne doit pas exister)."""

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_action(
    db: Session,
    action: str,
    *,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    ip_address: str | None = None,
    success: bool = True,
    details: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        success=success,
        details=details,
    )
    db.add(entry)
    return entry
