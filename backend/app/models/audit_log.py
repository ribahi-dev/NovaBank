"""Modèle AuditLog — le journal d'audit : qui a fait quoi, quand, d'où.

Rôle dans le domaine (cahier des charges, Modules 1 et 8) :
    En banque, la traçabilité est une obligation RÉGLEMENTAIRE, pas une
    option. Chaque action sensible (connexion réussie/échouée, création de
    transaction, clôture d'alerte...) laisse une trace horodatée avec
    l'adresse IP. En cas d'incident ou de fraude interne, ce journal est
    la première chose que les inspecteurs demandent.

Règle d'or : un journal d'audit est APPEND-ONLY.
    On INSÈRE, on ne modifie jamais, on ne supprime jamais. Aucun endpoint
    UPDATE/DELETE ne sera exposé sur cette table — un audit modifiable ne
    prouve plus rien.

Choix techniques à retenir :
    - user_id NULLABLE : une tentative de connexion avec un email inconnu
      doit être tracée alors qu'aucun utilisateur ne correspond.
    - String(45) pour l'IP : longueur maximale d'une adresse IPv6.
    - action en texte libre + entity_type/entity_id : pattern "audit
      polymorphe" — une seule table trace toutes les entités du système.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    # Ex. : "login_success", "login_failed", "transaction_created",
    # "alert_closed" — un vocabulaire fermé sera défini dans le service audit.
    action: Mapped[str] = mapped_column(String(100))

    # Sur QUOI l'action a porté : ("transaction", 42), ("alert", 7)...
    entity_type: Mapped[str | None] = mapped_column(String(100))
    entity_id: Mapped[int | None] = mapped_column(Integer)

    ip_address: Mapped[str | None] = mapped_column(String(45))

    # Trace aussi les ÉCHECS (login refusé, permission refusée) :
    # ce sont souvent les lignes les plus intéressantes pour la sécurité.
    success: Mapped[bool] = mapped_column(Boolean, default=True)

    details: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="audit_logs")
