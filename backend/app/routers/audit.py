"""Consultation du journal d'audit — Administrateur uniquement (CdC Module 8).

Lecture seule par construction : aucun endpoint de modification n'existe,
le journal est append-only côté application.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models import AuditLog

router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit"],
    dependencies=[Depends(require_role("admin"))],
)


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    ip_address: str | None
    success: bool
    details: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    db: Annotated[Session, Depends(get_db)],
    user_id: int | None = None,
    action: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    query = select(AuditLog)
    if user_id is not None:
        query = query.where(AuditLog.user_id == user_id)
    if action is not None:
        query = query.where(AuditLog.action == action)
    return db.scalars(
        query.order_by(AuditLog.created_at.desc()).offset(skip).limit(min(limit, 200))
    ).all()
