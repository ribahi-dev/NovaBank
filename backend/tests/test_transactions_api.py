"""Tests transactions : soldes, règles métier, scoring et alertes.

Le scénario "suspect" reproduit la démo de soutenance : gros montant par
rapport au revenu + changement de ville + fréquence élevée -> score >= 70
-> alerte créée automatiquement pour le directeur.
"""

from tests.test_clients_api import VALID_CLIENT


def _setup_account(client, headers, income="5000", balance="100000") -> int:
    client_id = client.post(
        "/clients", headers=headers, json={**VALID_CLIENT, "monthly_income": income}
    ).json()["id"]
    return client.post(
        "/accounts", headers=headers,
        json={"client_id": client_id, "initial_balance": balance},
    ).json()["id"]


def test_deposit_increases_balance_and_scores(client, auth_headers):
    headers = auth_headers("advisor")
    account_id = _setup_account(client, headers, balance="0")

    response = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "deposit", "amount": "500", "account_id": account_id,
              "city": "Casablanca"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["risk_score"] is not None  # chaque transaction est scorée
    assert body["risk_score"]["model_version"] == "mvp-rules-v1"
    assert client.get(f"/accounts/{account_id}", headers=headers).json()["balance"] == "500.00"


def test_withdrawal_insufficient_funds_400(client, auth_headers):
    headers = auth_headers("advisor")
    account_id = _setup_account(client, headers, balance="100")

    response = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "withdrawal", "amount": "500", "account_id": account_id},
    )

    assert response.status_code == 400
    assert "insuffisant" in response.json()["detail"].lower()


def test_transfer_moves_money_atomically(client, auth_headers):
    headers = auth_headers("advisor")
    source_id = _setup_account(client, headers, balance="1000")
    dest_id = _setup_account_second(client, headers)

    response = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "transfer", "amount": "400",
              "account_id": source_id, "destination_account_id": dest_id},
    )

    assert response.status_code == 201
    assert client.get(f"/accounts/{source_id}", headers=headers).json()["balance"] == "600.00"
    assert client.get(f"/accounts/{dest_id}", headers=headers).json()["balance"] == "400.00"


def _setup_account_second(client, headers) -> int:
    client_id = client.post(
        "/clients", headers=headers,
        json={**VALID_CLIENT, "cin": "ZZ999999", "first_name": "Omar", "last_name": "Tazi"},
    ).json()["id"]
    return client.post("/accounts", headers=headers, json={"client_id": client_id}).json()["id"]


def test_transfer_to_same_account_rejected_by_schema(client, auth_headers):
    headers = auth_headers("advisor")
    account_id = _setup_account(client, headers)

    response = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "transfer", "amount": "10",
              "account_id": account_id, "destination_account_id": account_id},
    )
    assert response.status_code == 422  # rejeté à la frontière, avant toute logique


def test_blocked_account_refuses_transactions(client, auth_headers):
    headers = auth_headers("advisor")
    account_id = _setup_account(client, headers)
    client.patch(f"/accounts/{account_id}", headers=headers, json={"status": "blocked"})

    response = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "deposit", "amount": "100", "account_id": account_id},
    )
    assert response.status_code == 400


def test_suspicious_transaction_creates_alert(client, auth_headers, db):
    headers = auth_headers("advisor")
    # Revenu 5000 MAD -> un virement de 45000 déclenche le facteur "montant".
    source_id = _setup_account(client, headers, income="5000", balance="100000")
    dest_id = _setup_account_second(client, headers)

    # Historique : 5 petites opérations à Casablanca (facteur fréquence
    # + ville de référence pour le facteur "changement de ville").
    for _ in range(5):
        client.post(
            "/transactions", headers=headers,
            json={"transaction_type": "deposit", "amount": "200",
                  "account_id": source_id, "city": "Casablanca"},
        )

    response = client.post(
        "/transactions", headers=headers,
        json={"transaction_type": "transfer", "amount": "45000",
              "account_id": source_id, "destination_account_id": dest_id,
              "city": "Tanger"},
    )

    assert response.status_code == 201
    risk = response.json()["risk_score"]
    assert risk["score"] >= 70
    assert "Tanger" in risk["explanation"]  # explication lisible (CdC §9.2)

    from app.models import Alert

    alerts = db.query(Alert).filter(Alert.alert_type == "transaction_risk").all()
    assert len(alerts) == 1
    assert alerts[0].status == "open"


def test_advisor_only_can_create(client, auth_headers):
    response = client.post(
        "/transactions", headers=auth_headers("director"),
        json={"transaction_type": "deposit", "amount": "10", "account_id": 1},
    )
    assert response.status_code == 403  # la saisie est un acte de conseiller
