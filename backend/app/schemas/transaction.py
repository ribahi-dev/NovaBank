"""Schemas Transaction — la réponse embarque le score IA calculé à la volée :
le conseiller voit immédiatement le verdict du moteur de risque."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TransactionCreate(BaseModel):
    transaction_type: str = Field(pattern="^(deposit|withdrawal|transfer)$")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)  # gt=0 : jamais nul ni négatif
    account_id: int
    destination_account_id: int | None = None
    city: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def check_transfer_destination(self):
        # Règle métier structurelle -> validée dès la frontière :
        # un virement exige une destination, les autres types l'interdisent.
        if self.transaction_type == "transfer":
            if self.destination_account_id is None:
                raise ValueError("Un virement exige destination_account_id")
            if self.destination_account_id == self.account_id:
                raise ValueError("Un virement vers le même compte est interdit")
        elif self.destination_account_id is not None:
            raise ValueError("destination_account_id n'a de sens que pour un virement")
        return self


class RiskScoreResponse(BaseModel):
    score: int
    confidence_level: str
    explanation: str
    model_version: str

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: Decimal
    city: str | None
    description: str | None
    account_id: int
    destination_account_id: int | None
    created_by_id: int
    created_at: datetime
    risk_score: RiskScoreResponse | None = None

    model_config = ConfigDict(from_attributes=True)
