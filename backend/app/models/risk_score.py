"""Modèle RiskScore — le verdict du module IA sur UNE transaction.

Rôle dans le domaine (cahier des charges, Modules 7 et 9.2) :
    Après chaque saisie de transaction, le moteur de scoring produit :
      - un score de 0 (normal) à 100 (très suspect) ;
      - un niveau de confiance ;
      - une EXPLICATION LISIBLE ("montant 3,2x supérieur aux habitudes...").
    L'explicabilité n'est pas un bonus : c'est une exigence réglementaire
    du secteur bancaire (RGPD, EU AI Act) — et l'argument fort du projet.

Choix techniques à retenir :
    - unique=True sur transaction_id : garantit le 1-1 côté BASE (le
      uselist=False côté Transaction n'est que la vue Python de cette
      contrainte). Une transaction = au plus un score.
    - model_version : TOUJOURS savoir quel modèle a produit un score
      (moteur de règles v1 ? Random Forest v2 ?). C'est la base du MLOps :
      sans version, impossible d'auditer ou de comparer les modèles.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(primary_key=True)

    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True)

    # Score entier 0-100 (format imposé par le cahier des charges §9.2 :
    # plus parlant pour un directeur d'agence qu'une probabilité 0-1).
    score: Mapped[int] = mapped_column(Integer)

    confidence_level: Mapped[str] = mapped_column(String(30))

    # Text (longueur illimitée) : l'explication peut citer plusieurs
    # facteurs ; String(255) serait trop court.
    explanation: Mapped[str] = mapped_column(Text)

    model_version: Mapped[str] = mapped_column(String(50), default="mvp-rules-v1")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    transaction = relationship("Transaction", back_populates="risk_score")
