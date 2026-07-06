"""Saisie et consultation des transactions (CdC Module 4).

La saisie est réservée au Conseiller (acteur défini au CdC §6.2) ; la
consultation est ouverte au Directeur également (pilotage).
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import require_role
from app.db.session import get_db
from app.models import Account, Transaction, User
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services import transaction_service
from app.services.transaction_service import BusinessRuleError

router = APIRouter(prefix="/transactions", tags=["Transactions"])

Advisor = Annotated[User, Depends(require_role("advisor"))]
Staff = Annotated[User, Depends(require_role("advisor", "director"))]


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    data: TransactionCreate, request: Request,
    db: Annotated[Session, Depends(get_db)], advisor: Advisor,
):
    try:
        transaction = transaction_service.create_transaction(
            db, data, advisor, ip_address=request.client.host if request.client else None
        )
    except BusinessRuleError as exc:
        # Règle métier violée = 400 : la requête est bien formée (sinon 422),
        # mais l'état du domaine la refuse (solde, statut du compte...).
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return transaction


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    db: Annotated[Session, Depends(get_db)],
    staff: Staff,
    account_id: int | None = None,
    client_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
):
    # selectinload : charge les scores en UNE requête supplémentaire au lieu
    # d'une par transaction (anti-pattern N+1).
    query = select(Transaction).options(selectinload(Transaction.risk_score))
    if account_id is not None:
        query = query.where(Transaction.account_id == account_id)
    if client_id is not None:
        query = query.join(Account, Transaction.account_id == Account.id).where(
            Account.client_id == client_id
        )
    if date_from is not None:
        query = query.where(Transaction.created_at >= date_from)
    if date_to is not None:
        query = query.where(Transaction.created_at <= date_to)
    return db.scalars(
        query.order_by(Transaction.created_at.desc()).offset(skip).limit(min(limit, 100))
    ).all()
