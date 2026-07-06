"""Dépendances FastAPI transverses : utilisateur courant et contrôle RBAC.

Chaîne d'authentification sur chaque requête protégée :
  Header Authorization: Bearer <token>
    -> oauth2_scheme extrait le token
    -> get_current_user vérifie signature/expiration puis charge le User
    -> require_role vérifie l'AUTORISATION (distincte de l'authentification,
       vérifiée à chaque requête côté serveur — CdC §5.2 et Module 8).
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Jeton invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token, expected_type="access")
    except jwt.InvalidTokenError:
        raise credentials_error

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):
    """Fabrique de dépendance : `Depends(require_role("admin", "director"))`.

    401 = "qui es-tu ?" (non authentifié) ; 403 = "je sais qui tu es,
    mais tu n'as pas le droit" (non autorisé). Ne pas les confondre.
    """

    def checker(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle",
            )
        return current_user

    return checker
