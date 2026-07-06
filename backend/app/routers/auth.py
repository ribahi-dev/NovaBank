"""Endpoints d'authentification : login (OAuth2 password flow) et refresh."""

from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.session import get_db
from app.models import User
from app.schemas.auth import RefreshRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser):
    """Profil de l'utilisateur connecté — utilisé par le frontend pour
    afficher le nom/rôle et construire le menu adapté."""
    return current_user


@router.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    # OAuth2PasswordRequestForm impose le champ "username" : c'est l'email ici.
    ip = request.client.host if request.client else None
    try:
        user = auth_service.authenticate(db, form.username, form.password, ip)
    except auth_service.AccountLockedError as exc:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc))
    except auth_service.AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide")

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inconnu ou désactivé")

    # Rotation : un nouveau couple access+refresh à chaque renouvellement.
    return TokenResponse(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )
