"""Schemas d'authentification (réponse de login et corps de refresh)."""

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # convention OAuth2 attendue par les clients


class RefreshRequest(BaseModel):
    refresh_token: str
