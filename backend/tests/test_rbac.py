"""Tests RBAC : 401 sans jeton, 403 pour un rôle insuffisant."""


def test_endpoints_require_authentication(client):
    assert client.get("/clients").status_code == 401
    assert client.get("/users").status_code == 401
    assert client.get("/alerts").status_code == 401


def test_advisor_cannot_manage_users(client, auth_headers):
    response = client.get("/users", headers=auth_headers("advisor"))
    assert response.status_code == 403  # authentifié mais non autorisé


def test_advisor_cannot_access_director_dashboard(client, auth_headers):
    assert client.get("/analytics/kpi", headers=auth_headers("advisor")).status_code == 403
    assert client.get("/alerts", headers=auth_headers("advisor")).status_code == 403


def test_admin_creates_user(client, auth_headers):
    response = client.post(
        "/users",
        headers=auth_headers("admin"),
        json={
            "first_name": "Yasmine",
            "last_name": "Idrissi",
            "email": "yasmine@novabank.ma",
            "password": "MotDePasse#2026",
            "role": "director",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "director"
    assert "password" not in body and "password_hash" not in body  # jamais exposé


def test_duplicate_email_conflict(client, auth_headers):
    headers = auth_headers("admin")
    payload = {
        "first_name": "A", "last_name": "B",
        "email": "double@novabank.ma", "password": "MotDePasse#2026", "role": "advisor",
    }
    assert client.post("/users", headers=headers, json=payload).status_code == 201
    assert client.post("/users", headers=headers, json=payload).status_code == 409
