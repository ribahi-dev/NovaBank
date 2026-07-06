"""Modèle Client — le client bancaire (simulé) de l'agence.

Rôle dans le domaine (cahier des charges, Module 2) :
    Un client possède un ou plusieurs comptes ; le conseiller peut le
    rechercher par nom ou CIN, consulter sa fiche, et le DÉSACTIVER
    (suppression logique via is_active — jamais de DELETE physique :
    l'historique bancaire doit rester intact pour l'audit).

Choix techniques à retenir :
    - Numeric(12, 2) pour l'argent, JAMAIS Float : un float binaire ne sait
      pas représenter 0.10 exactement — les erreurs d'arrondi s'accumulent,
      inacceptable en banque. Numeric = décimal exact.
    - server_default=func.now() : l'horodatage est produit par POSTGRESQL,
      pas par Python. Une seule horloge de référence pour tout le système
      (deux serveurs API auraient deux horloges légèrement différentes).
    - `Mapped[str | None]` = colonne NULLABLE ; `Mapped[str]` = NOT NULL.
      Le type Python déclare l'intention, SQLAlchemy génère la contrainte.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Client(Base):
    __tablename__ = "clients"

    # primary_key=True crée déjà un index unique — inutile d'ajouter index=True.
    id: Mapped[int] = mapped_column(primary_key=True)

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    # CIN = identifiant national marocain, unique par personne (exigence KYC).
    # index=True car c'est LE critère de recherche du conseiller (Module 2).
    cin: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(255))

    # Profession et revenu : features importantes pour le module IA
    # (écart entre le montant d'une transaction et le profil du client).
    profession: Mapped[str | None] = mapped_column(String(100))
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))

    # Suppression logique : un client désactivé disparaît des écrans mais
    # reste en base (intégrité référentielle + audit réglementaire).
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relation 1-N : UN client possède PLUSIEURS comptes.
    # back_populates lie les deux sens : client.accounts <-> account.client.
    # C'est un attribut Python (navigation objet), pas une colonne SQL —
    # la clé étrangère, elle, vit côté Account (accounts.client_id).
    accounts = relationship("Account", back_populates="client")
