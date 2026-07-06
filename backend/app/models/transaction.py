"""Modèle Transaction — dépôt, retrait ou virement saisi par un conseiller.

Rôle dans le domaine (cahier des charges, Module 4) :
    C'est l'entité CENTRALE du projet : chaque transaction créée déclenche
    le scoring IA (Module 7), qui peut générer une alerte (Module 9).
    Le dashboard (Module 5) et l'analytics (Module 6) agrègent cette table.

Modélisation du virement :
    Un virement implique DEUX comptes -> deux clés étrangères vers accounts :
      - account_id             : compte source (toujours renseigné) ;
      - destination_account_id : compte cible (NULL pour dépôt/retrait).
    C'est le pattern classique "self-referencing pair" d'un livre bancaire.

Traçabilité (exigence Module 8) :
    created_by_id enregistre QUEL conseiller a saisi l'opération — en
    banque, toute opération doit être imputable à une personne.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)

    transaction_type: Mapped[str] = mapped_column(
        Enum("deposit", "withdrawal", "transfer", name="transaction_type"),
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))

    # La ville de l'opération : feature clé du module IA ("changement de
    # ville par rapport aux habitudes du client" — cahier des charges §9.1).
    city: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))

    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    destination_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # foreign_keys en syntaxe LISTE (les colonnes sont définies juste
    # au-dessus, on les référence directement) : lève l'ambiguïté des deux
    # FK vers accounts — voir le commentaire miroir dans account.py.
    account = relationship("Account", foreign_keys=[account_id], back_populates="transactions")
    destination_account = relationship("Account", foreign_keys=[destination_account_id])
    created_by = relationship("User", back_populates="transactions")

    # uselist=False transforme la relation 1-N en 1-1 : UNE transaction a
    # AU PLUS UN score (garanti côté base par le unique=True de
    # risk_scores.transaction_id). transaction.risk_score renvoie donc un
    # objet, pas une liste.
    risk_score = relationship("RiskScore", back_populates="transaction", uselist=False)

    # 1-N : une transaction peut déclencher plusieurs alertes
    # (ex. risque IA + seuil réglementaire).
    alerts = relationship("Alert", back_populates="transaction")
