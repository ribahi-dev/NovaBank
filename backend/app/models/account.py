"""Modèle Account — le compte bancaire rattaché à un client.

Rôle dans le domaine (cahier des charges, Module 3) :
    Créé par un conseiller pour un client existant. Porte le solde et le
    statut (active/blocked/closed). Toutes les transactions s'y rattachent.

Choix techniques à retenir :
    - Le solde est STOCKÉ ici (dénormalisation assumée pour la performance :
      pas besoin de sommer des milliers de transactions à chaque affichage).
      CONTREPARTIE : sa mise à jour devra être atomique et verrouillée
      (SELECT ... FOR UPDATE dans le service de virement, Phase B6) pour
      éviter qu'un virement concurrent ne corrompe le solde.
    - Enum SQL : PostgreSQL rejettera physiquement toute valeur hors liste —
      la base se défend elle-même, même si un bug contourne la validation
      Python. `name=` est le nom du type ENUM créé côté PostgreSQL.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 34 caractères = longueur maximale d'un IBAN (format international).
    # unique + index : c'est un critère de recherche du Module 2.
    account_number: Mapped[str] = mapped_column(String(34), unique=True, index=True)

    account_type: Mapped[str] = mapped_column(
        Enum("current", "savings", name="account_type"),
        default="current",
    )

    # Numeric(14, 2) : jusqu'à 999 999 999 999,99 — jamais Float pour l'argent.
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)

    status: Mapped[str] = mapped_column(
        Enum("active", "blocked", "closed", name="account_status"),
        default="active",
    )

    # LA clé étrangère qui matérialise "un compte appartient à un client".
    # PostgreSQL refusera un client_id qui n'existe pas dans clients.id
    # (intégrité référentielle garantie par la base, pas par le code).
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Sens N-1 de la relation : account.client renvoie l'objet Client.
    client = relationship("Client", back_populates="accounts")

    # foreign_keys est OBLIGATOIRE ici : Transaction possède DEUX clés
    # étrangères vers accounts (account_id = source, destination_account_id
    # = cible du virement). Sans cette précision, SQLAlchemy ne sait pas
    # laquelle utiliser pour "les transactions de ce compte" et lève une
    # AmbiguousForeignKeysError au démarrage.
    transactions = relationship(
        "Transaction",
        back_populates="account",
        foreign_keys="Transaction.account_id",
    )
