"""Tests des rapports serveur (PDF + Excel) et de leur contrôle d'accès."""

from tests.test_clients_api import VALID_CLIENT


def _seed_one_transaction(client, advisor_headers):
    cid = client.post("/clients", headers=advisor_headers, json=VALID_CLIENT).json()["id"]
    aid = client.post(
        "/accounts", headers=advisor_headers, json={"client_id": cid, "initial_balance": "1000"}
    ).json()["id"]
    client.post(
        "/transactions", headers=advisor_headers,
        json={"transaction_type": "deposit", "amount": "500", "account_id": aid, "city": "Rabat"},
    )


def test_pdf_report_downloads(client, auth_headers):
    advisor = auth_headers("advisor")
    _seed_one_transaction(client, advisor)

    response = client.get("/reports/activity.pdf", headers=auth_headers("director"))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # Signature d'un fichier PDF : commence par "%PDF".
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 1000


def test_xlsx_report_downloads(client, auth_headers):
    advisor = auth_headers("advisor")
    _seed_one_transaction(client, advisor)

    response = client.get("/reports/transactions.xlsx", headers=auth_headers("director"))

    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    # Un .xlsx est un ZIP : commence par "PK".
    assert response.content[:2] == b"PK"


def test_reports_require_director_or_admin(client, auth_headers):
    # Un conseiller n'a pas accès aux rapports (réservés direction/admin).
    assert client.get("/reports/activity.pdf", headers=auth_headers("advisor")).status_code == 403
    assert client.get("/reports/transactions.xlsx", headers=auth_headers("advisor")).status_code == 403


def test_reports_require_authentication(client):
    assert client.get("/reports/activity.pdf").status_code == 401
