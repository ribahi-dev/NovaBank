"""Tests comptes bancaires : création, numérotation système, statut."""

from tests.test_clients_api import VALID_CLIENT


def _create_client(client, headers) -> int:
    return client.post("/clients", headers=headers, json=VALID_CLIENT).json()["id"]


def test_create_account_with_generated_number(client, auth_headers):
    headers = auth_headers("advisor")
    client_id = _create_client(client, headers)

    response = client.post(
        "/accounts", headers=headers,
        json={"client_id": client_id, "account_type": "current", "initial_balance": "1000"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["account_number"].startswith("NB") and len(body["account_number"]) == 14
    assert body["balance"] == "1000.00"
    assert body["status"] == "active"


def test_account_for_unknown_client_404(client, auth_headers):
    response = client.post(
        "/accounts", headers=auth_headers("advisor"), json={"client_id": 99999}
    )
    assert response.status_code == 404


def test_block_account(client, auth_headers):
    headers = auth_headers("advisor")
    client_id = _create_client(client, headers)
    account_id = client.post("/accounts", headers=headers, json={"client_id": client_id}).json()["id"]

    response = client.patch(f"/accounts/{account_id}", headers=headers, json={"status": "blocked"})

    assert response.status_code == 200
    assert response.json()["status"] == "blocked"


def test_list_accounts_by_client(client, auth_headers):
    headers = auth_headers("advisor")
    client_id = _create_client(client, headers)
    client.post("/accounts", headers=headers, json={"client_id": client_id})
    client.post("/accounts", headers=headers, json={"client_id": client_id, "account_type": "savings"})

    accounts = client.get("/accounts", headers=headers, params={"client_id": client_id}).json()
    assert len(accounts) == 2
