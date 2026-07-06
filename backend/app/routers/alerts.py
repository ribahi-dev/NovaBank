"""Centre d'alertes — réservé au Directeur d'agence (CdC Module 9).

Cycle de vie : open -> in_progress -> closed (machine à états du
diagramme d'activité UML §7.4). Une alerte fermée est définitive.
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import require_role
from app.db.session import get_db
from app.models import Alert, Transaction, User
from app.schemas.alert import AlertResponse, AlertUpdate
from app.services import audit_service

router = APIRouter(
    prefix="/alerts",
    tags=["Alertes"],
    dependencies=[Depends(require_role("director"))],
)

_load_detail = selectinload(Alert.transaction).selectinload(Transaction.risk_score)


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    db: Annotated[Session, Depends(get_db)],
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    query = select(Alert).options(_load_detail)
    if status_filter is not None:
        query = query.where(Alert.status == status_filter)
    return db.scalars(
        query.order_by(Alert.created_at.desc()).offset(skip).limit(min(limit, 100))
    ).all()


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Annotated[Session, Depends(get_db)]):
    alert = db.scalar(select(Alert).options(_load_detail).where(Alert.id == alert_id))
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
def update_alert_status(
    alert_id: int, data: AlertUpdate, request: Request,
    db: Annotated[Session, Depends(get_db)],
    director: Annotated[User, Depends(require_role("director"))],
):
    alert = db.scalar(select(Alert).options(_load_detail).where(Alert.id == alert_id))
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alerte introuvable")
    if alert.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Une alerte clôturée ne peut plus être modifiée",
        )

    alert.status = data.status
    if data.status == "closed":
        alert.closed_at = datetime.now(timezone.utc)

    audit_service.log_action(
        db, "alert_status_changed", user_id=director.id, entity_type="alert",
        entity_id=alert.id, ip_address=request.client.host if request.client else None,
        details=f"nouveau statut : {data.status}",
    )
    db.commit()
    db.refresh(alert)
    return alert
