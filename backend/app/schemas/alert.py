"""Schemas Alert — le directeur ne peut modifier QUE le statut (machine à états)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.transaction import TransactionResponse


class AlertUpdate(BaseModel):
    status: str = Field(pattern="^(in_progress|closed)$")  # "open" n'est jamais re-forçable


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    level: str
    message: str
    status: str
    transaction_id: int | None
    created_at: datetime
    closed_at: datetime | None
    # Détail complet pour l'écran d'alerte du directeur (transaction + score)
    transaction: TransactionResponse | None = None

    model_config = ConfigDict(from_attributes=True)
