"""Schemas User — noter l'ABSENCE totale de password_hash en sortie."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Regex e-mail simple (le vrai contrôle, c'est l'unicité en base ;
# évite la dépendance email-validator pour un format jamais parfait).
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=255, pattern=EMAIL_PATTERN)
    # Le mot de passe n'existe QUE dans le schema d'entrée : haché
    # immédiatement, jamais stocké ni renvoyé.
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern="^(admin|director|advisor)$", default="advisor")


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = Field(default=None, pattern="^(admin|director|advisor)$")
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
