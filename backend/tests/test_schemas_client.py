"""Tests des schemas Client — la validation est du CODE, donc on la teste.

Ces tests ne touchent ni HTTP ni la base : on vérifie le contrat pur
(qu'est-ce qui passe, qu'est-ce qui est rejeté, qu'est-ce qui est ignoré).
C'est la couche de tests la plus rapide et la plus stable du projet.
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate

# Un payload valide de référence : chaque test le copie et casse UN champ.
# (pattern "fixture de base" — si le schéma évolue, on ne corrige qu'ici)
VALID = {
    "first_name": "Amina",
    "last_name": "Benali",
    "cin": "AB123456",
    "phone": "0661234567",
    "profession": "Enseignante",
    "monthly_income": "8500.50",  # str volontaire : Pydantic doit convertir
}


def test_create_valid_payload():
    client = ClientCreate(**VALID)

    # La conversion str -> Decimal prouve que le parsing a eu lieu
    # (pas un simple passage de valeurs).
    assert client.monthly_income == Decimal("8500.50")
    assert client.cin == "AB123456"


def test_create_missing_required_field_rejected():
    payload = {k: v for k, v in VALID.items() if k != "cin"}

    # pytest.raises : le test RÉUSSIT si l'exception est levée —
    # on teste le comportement d'échec, aussi important que le succès.
    with pytest.raises(ValidationError):
        ClientCreate(**payload)


def test_create_invalid_cin_format_rejected():
    with pytest.raises(ValidationError):
        ClientCreate(**{**VALID, "cin": "123456"})  # ne commence pas par une lettre


def test_create_negative_income_rejected():
    with pytest.raises(ValidationError):
        ClientCreate(**{**VALID, "monthly_income": "-1000"})


def test_create_ignores_system_fields():
    # Un client HTTP malveillant envoie id/is_active : Pydantic les IGNORE
    # (ils ne font pas partie du contrat ClientCreate) — c'est la parade
    # au "mass assignment" (OWASP API n°3).
    client = ClientCreate(**VALID, id=999, is_active=False)
    assert not hasattr(client, "id")
    assert not hasattr(client, "is_active")


def test_update_partial_only_sends_set_fields():
    update = ClientUpdate(phone="0700000000")

    # exclude_unset : seuls les champs EXPLICITEMENT envoyés apparaissent —
    # c'est ce que le CRUD utilisera pour un PATCH partiel correct.
    assert update.model_dump(exclude_unset=True) == {"phone": "0700000000"}


def test_response_reads_orm_object():
    # Objet SQLAlchemy construit EN MÉMOIRE (id/created_at posés à la main,
    # comme la base l'aurait fait) : aucun PostgreSQL requis ici.
    orm_client = Client(
        id=1,
        first_name="Amina",
        last_name="Benali",
        cin="AB123456",
        is_active=True,
        created_at=datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc),
    )

    response = ClientResponse.model_validate(orm_client)  # grâce à from_attributes

    assert response.id == 1
    assert response.created_at.year == 2026
