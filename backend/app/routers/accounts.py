"""Gestion des comptes bancaires — Conseiller et Directeur (CdC Module 3)."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models import Account, Client, User
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services import audit_service

router = APIRouter(prefix="/accounts", tags=["Comptes"])

Staff = Annotated[User, Depends(require_role("advisor", "director"))]


def _generate_account_number(db: Session) -> str:
    """Numéro type 'NB' + 12 chiffres, généré par le SYSTÈME (jamais par
    l'appelant) et garanti unique par re-tirage en cas de collision."""
    while True:
        number = "NB" + "".join(str(secrets.randbelow(10)) for _ in range(12))
        if not db.scalar(select(Account).where(Account.account_number == number)):
            return number


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    data: AccountCreate, request: Request, db: Annotated[Session, Depends(get_db)], staff: Staff
):
    client = db.get(Client, data.client_id)
    if client is None or not client.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable ou inactif")

    account = Account(
        account_number=_generate_account_number(db),
        account_type=data.account_type,
        balance=data.initial_balance,
        client_id=data.client_id,
    )
    db.add(account)
    db.flush()
    audit_service.log_action(
        db, "account_created", user_id=staff.id, entity_type="account", entity_id=account.id,
        ip_address=request.client.host if request.client else None,
        details=f"{account.account_number} ({account.account_type}), solde initial {account.balance}",
    )
    db.commit()
    db.refresh(account)
    return account


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    db: Annotated[Session, Depends(get_db)],
    staff: Staff,
    client_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
):
    query = select(Account)
    if client_id is not None:
        query = query.where(Account.client_id == client_id)
    return db.scalars(query.order_by(Account.id).offset(skip).limit(min(limit, 100))).all()


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Annotated[Session, Depends(get_db)], staff: Staff):
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")
    return account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int, data: AccountUpdate, request: Request,
    db: Annotated[Session, Depends(get_db)], staff: Staff,
):
    account = db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(account, field, value)
    audit_service.log_action(
        db, "account_updated", user_id=staff.id, entity_type="account", entity_id=account.id,
        ip_address=request.client.host if request.client else None,
        details=f"champs modifiés : {', '.join(changes) or 'aucun'}",
    )
    db.commit()
    db.refresh(account)
    return account
