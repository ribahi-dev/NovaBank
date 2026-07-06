"""Gestion des utilisateurs de la plateforme — réservé à l'Administrateur."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.core.security import hash_password
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services import audit_service

router = APIRouter(
    prefix="/users",
    tags=["Utilisateurs"],
    dependencies=[Depends(require_role("admin"))],  # RBAC sur TOUT le router
)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_role("admin"))],
):
    if db.scalar(select(User).where(User.email == data.email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé")

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),  # le mot de passe meurt ici
        role=data.role,
    )
    db.add(user)
    db.flush()
    audit_service.log_action(
        db, "user_created", user_id=admin.id, entity_type="user", entity_id=user.id,
        ip_address=request.client.host if request.client else None,
        details=f"création de {user.email} ({user.role})",
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UserResponse])
def list_users(db: Annotated[Session, Depends(get_db)], skip: int = 0, limit: int = 50):
    return db.scalars(select(User).order_by(User.id).offset(skip).limit(min(limit, 100))).all()


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    admin: Annotated[User, Depends(require_role("admin"))],
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(user, field, value)

    audit_service.log_action(
        db, "user_updated", user_id=admin.id, entity_type="user", entity_id=user.id,
        ip_address=request.client.host if request.client else None,
        details=f"champs modifiés : {', '.join(changes) or 'aucun'}",
    )
    db.commit()
    db.refresh(user)
    return user
