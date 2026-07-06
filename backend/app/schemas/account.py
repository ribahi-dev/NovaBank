"""Schemas Account — le numéro de compte et le solde sont décidés par le
système : l'appelant fournit seulement le client, le type et le dépôt initial."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    client_id: int
    account_type: str = Field(pattern="^(current|savings)$", default="current")
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)


class AccountUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(active|blocked|closed)$")


class AccountResponse(BaseModel):
    id: int
    account_number: str
    account_type: str
    balance: Decimal
    status: str
    client_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
