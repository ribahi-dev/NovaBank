"""Primitives de sécurité : hachage bcrypt des mots de passe et JWT.

- bcrypt via pwdlib (exigence CdC §8.4) : hachage à sens unique + sel.
- JWT signés HS256 : access token court (authentification stateless) +
  refresh token long (renouvellement sans re-login). Le type est encodé
  dans le payload pour qu'un refresh token ne puisse JAMAIS servir
  d'access token (bonne pratique OWASP citée au CdC §5.2).
"""

from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

_hasher = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def _create_token(user_id: int, token_type: str, lifetime: timedelta, role: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),      # subject : l'identifiant de l'utilisateur
        "type": token_type,       # "access" ou "refresh" — jamais interchangeables
        "iat": now,
        "exp": now + lifetime,
    }
    if role is not None:
        payload["role"] = role
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(user_id, "access", timedelta(minutes=settings.access_token_expire_minutes), role)


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str, expected_type: str) -> dict:
    """Vérifie signature + expiration + type. Lève jwt.InvalidTokenError sinon.

    algorithms=[...] est OBLIGATOIRE : sans cette liste blanche, un jeton
    forgé avec alg='none' serait accepté (attaque classique, OWASP §5.2).
    """
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Jeton de type inattendu (attendu : {expected_type})")
    return payload
