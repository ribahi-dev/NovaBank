"""Tests d'authentification : login, verrouillage anti force-brute, refresh."""

from app.core.config import settings
from tests.conftest import TEST_PASSWORD


def test_login_success_returns_tokens(client, make_user):
    user = make_user("advisor")
    response = client.post("/auth/login", data={"username": user.email, "password": TEST_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_wrong_password_is_generic_401(client, make_user):
    user = make_user("advisor")
    response = client.post("/auth/login", data={"username": user.email, "password": "mauvais"})

    assert response.status_code == 401
    # Même message que pour un email inconnu : pas d'énumération d'utilisateurs.
    assert response.json()["detail"] == "Email ou mot de passe incorrect"


def test_login_unknown_email_same_message(client):
    response = client.post("/auth/login", data={"username": "ghost@novabank.ma", "password": "x"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou mot de passe incorrect"


def test_account_locks_after_max_failures(client, make_user, db):
    user = make_user("advisor")
    for _ in range(settings.max_failed_login_attempts):
        client.post("/auth/login", data={"username": user.email, "password": "mauvais"})

    # Même le BON mot de passe est refusé pendant le verrouillage (423 Locked).
    response = client.post("/auth/login", data={"username": user.email, "password": TEST_PASSWORD})
    assert response.status_code == 423

    # Une alerte de sécurité a été créée pour le directeur.
    from app.models import Alert

    alerts = db.query(Alert).filter(Alert.alert_type == "login_security").all()
    assert len(alerts) == 1


def test_refresh_returns_new_tokens(client, make_user):
    user = make_user("advisor")
    login = client.post("/auth/login", data={"username": user.email, "password": TEST_PASSWORD}).json()

    response = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_me_returns_profile_without_secrets(client, make_user):
    user = make_user("director")
    login = client.post("/auth/login", data={"username": user.email, "password": TEST_PASSWORD}).json()

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {login['access_token']}"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == user.email and body["role"] == "director"
    assert "password_hash" not in body


def test_refresh_token_cannot_be_used_as_access_token(client, make_user):
    user = make_user("advisor")
    login = client.post("/auth/login", data={"username": user.email, "password": TEST_PASSWORD}).json()

    # Un refresh token présenté comme access token doit être rejeté (type vérifié).
    response = client.get("/clients", headers={"Authorization": f"Bearer {login['refresh_token']}"})
    assert response.status_code == 401
