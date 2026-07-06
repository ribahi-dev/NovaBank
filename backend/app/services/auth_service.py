"""Service d'authentification — login avec verrouillage anti force-brute.

Règles (CdC Modules 1 et 8) :
  - mots de passe vérifiés via bcrypt, jamais comparés en clair ;
  - après N échecs consécutifs, compte verrouillé pendant M minutes
    (même le bon mot de passe est refusé pendant le verrouillage) ;
  - chaque tentative (succès OU échec) est journalisée avec l'IP ;
  - au 1er verrouillage, une alerte de sécurité est créée pour le directeur.

Piège évité : le message d'erreur est IDENTIQUE pour "email inconnu" et
"mot de passe faux" — sinon l'API révélerait quels emails existent
(énumération d'utilisateurs, OWASP).
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Alert, User
from app.core.security import verify_password
from app.services import audit_service


class AuthenticationError(Exception):
    """Échec d'authentification — traduit en HTTP 401 par le router."""


class AccountLockedError(Exception):
    """Compte temporairement verrouillé — traduit en HTTP 423 (Locked)."""


GENERIC_MESSAGE = "Email ou mot de passe incorrect"


def authenticate(db: Session, email: str, password: str, ip_address: str | None = None) -> User:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        # Journaliser même les tentatives sur des comptes inexistants
        # (repérage des campagnes de force brute par IP).
        audit_service.log_action(
            db, "login_failed", ip_address=ip_address, success=False,
            details=f"email inconnu : {email}",
        )
        db.commit()
        raise AuthenticationError(GENERIC_MESSAGE)

    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        audit_service.log_action(
            db, "login_rejected_locked", user_id=user.id,
            ip_address=ip_address, success=False,
        )
        db.commit()
        raise AccountLockedError("Compte temporairement verrouillé suite à des échecs répétés")

    if not user.is_active or not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        details = f"échec n°{user.failed_login_attempts}"
        if user.failed_login_attempts >= settings.max_failed_login_attempts:
            user.locked_until = now + timedelta(minutes=settings.lockout_minutes)
            user.failed_login_attempts = 0
            details += f" -> verrouillage {settings.lockout_minutes} min"
            db.add(
                Alert(
                    alert_type="login_security",
                    level="high",
                    message=(
                        f"Compte {user.email} verrouillé après échecs de connexion "
                        f"répétés (IP : {ip_address or 'inconnue'})"
                    ),
                )
            )
        audit_service.log_action(
            db, "login_failed", user_id=user.id, ip_address=ip_address,
            success=False, details=details,
        )
        db.commit()
        raise AuthenticationError(GENERIC_MESSAGE)

    # Succès : remise à zéro du compteur d'échecs.
    user.failed_login_attempts = 0
    user.locked_until = None
    audit_service.log_action(db, "login_success", user_id=user.id, ip_address=ip_address)
    db.commit()
    return user
