"""Modèle User — l'utilisateur DE LA PLATEFORME (pas le client bancaire).

Distinction fondamentale :
    User   = qui se CONNECTE à l'application (conseiller, directeur, admin) ;
    Client = qui possède des comptes à la banque.
    Les confondre est l'erreur de modélisation n°1 dans ce type de projet.

Rôle dans le domaine (cahier des charges, Modules 1 et 8) :
    Porte l'authentification (email + mot de passe HACHÉ), le rôle RBAC,
    et le mécanisme de verrouillage après échecs de connexion répétés.

Choix techniques à retenir :
    - password_hash : on ne stocke JAMAIS le mot de passe, seulement son
      hachage bcrypt (fonction à sens unique + sel aléatoire). Même l'admin
      de la base ne peut pas retrouver le mot de passe d'un utilisateur.
    - role en Enum : 3 rôles fixes suffisent au MVP. L'évolution vers des
      tables role/permission dynamiques est documentée dans
      docs/schema_cible.sql (argument d'évolutivité en soutenance).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    # L'email sert d'identifiant de connexion -> unique + indexé
    # (le login fait un SELECT ... WHERE email = ... à chaque connexion).
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # 255 caractères : les hachages bcrypt font ~60 caractères, la marge
    # permet de changer d'algorithme (Argon2...) sans migration de schéma.
    password_hash: Mapped[str] = mapped_column(String(255))

    role: Mapped[str] = mapped_column(
        Enum("admin", "director", "advisor", name="user_role"),
        default="advisor",
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Anti force-brute (cahier des charges, Module 8) : on compte les échecs
    # de connexion ; au-delà du seuil, locked_until est posé et le login est
    # refusé jusqu'à cette date, même avec le bon mot de passe.
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Traçabilité : toutes les transactions saisies et toutes les actions
    # auditées de cet utilisateur.
    transactions = relationship("Transaction", back_populates="created_by")
    audit_logs = relationship("AuditLog", back_populates="user")
