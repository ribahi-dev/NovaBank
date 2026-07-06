"""Gestion des clients bancaires — Conseiller et Directeur (CdC Module 2)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models import Client, User
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.services import audit_service

router = APIRouter(prefix="/clients", tags=["Clients"])

# Dépendance partagée : conseiller OU directeur (l'admin gère la plateforme,
# pas la clientèle — séparation des responsabilités du CdC §6.1).
Staff = Annotated[User, Depends(require_role("advisor", "director"))]


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    data: ClientCreate, request: Request, db: Annotated[Session, Depends(get_db)], staff: Staff
):
    if db.scalar(select(Client).where(Client.cin == data.cin)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un client avec ce CIN existe déjà")

    client = Client(**data.model_dump())
    db.add(client)
    db.flush()
    audit_service.log_action(
        db, "client_created", user_id=staff.id, entity_type="client", entity_id=client.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=list[ClientResponse])
def list_clients(
    db: Annotated[Session, Depends(get_db)],
    staff: Staff,
    search: str | None = None,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 50,
):
    query = select(Client)
    if not include_inactive:
        query = query.where(Client.is_active.is_(True))
    if search:
        # Recherche par nom, prénom ou CIN (CdC Module 2), insensible à la casse.
        pattern = f"%{search}%"
        query = query.where(
            or_(
                Client.first_name.ilike(pattern),
                Client.last_name.ilike(pattern),
                Client.cin.ilike(pattern),
            )
        )
    return db.scalars(query.order_by(Client.id).offset(skip).limit(min(limit, 100))).all()


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: int, db: Annotated[Session, Depends(get_db)], staff: Staff):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return client


@router.patch("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int, data: ClientUpdate, request: Request,
    db: Annotated[Session, Depends(get_db)], staff: Staff,
):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(client, field, value)
    audit_service.log_action(
        db, "client_updated", user_id=staff.id, entity_type="client", entity_id=client.id,
        ip_address=request.client.host if request.client else None,
        details=f"champs modifiés : {', '.join(changes) or 'aucun'}",
    )
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_client(
    client_id: int, request: Request, db: Annotated[Session, Depends(get_db)], staff: Staff
):
    """Suppression LOGIQUE uniquement (CdC Module 2) : le client disparaît
    des listes mais son historique reste intact pour l'audit."""
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    client.is_active = False
    audit_service.log_action(
        db, "client_deactivated", user_id=staff.id, entity_type="client", entity_id=client.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
