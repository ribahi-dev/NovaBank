"""Tests du centre d'alertes et du dashboard directeur."""

from tests.test_clients_api import VALID_CLIENT


def _create_suspicious_alert(client, advisor_headers):
    """Rejoue le scénario suspect pour générer une alerte réelle."""
    client_id = client.post(
        "/clients", headers=advisor_headers, json={**VALID_CLIENT, "monthly_income": "4000"}
    ).json()["id"]
    account_id = client.post(
        "/accounts", headers=advisor_headers,
        json={"client_id": client_id, "initial_balance": "90000"},
    ).json()["id"]
    for _ in range(5):
        client.post(
            "/transactions", headers=advisor_headers,
            json={"transaction_type": "deposit", "amount": "150",
                  "account_id": account_id, "city": "Casablanca"},
        )
    client.post(
        "/transactions", headers=advisor_headers,
        json={"transaction_type": "withdrawal", "amount": "40000",
              "account_id": account_id, "city": "Agadir"},
    )


def test_director_alert_lifecycle(client, auth_headers):
    advisor = auth_headers("advisor")
    director = auth_headers("director")
    _create_suspicious_alert(client, advisor)

    # 1. L'alerte apparaît dans la liste des alertes ouvertes.
    alerts = client.get("/alerts", headers=director, params={"status_filter": "open"}).json()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["level"] in ("high", "critical")
    # Le détail embarque la transaction ET son explication IA.
    assert alert["transaction"]["risk_score"]["score"] >= 70

    # 2. Prise en charge puis clôture.
    taken = client.patch(f"/alerts/{alert['id']}", headers=director, json={"status": "in_progress"})
    assert taken.status_code == 200

    closed = client.patch(f"/alerts/{alert['id']}", headers=director, json={"status": "closed"})
    assert closed.status_code == 200
    assert closed.json()["closed_at"] is not None

    # 3. Une alerte clôturée est immuable.
    reopen = client.patch(f"/alerts/{alert['id']}", headers=director, json={"status": "in_progress"})
    assert reopen.status_code == 409


def test_kpi_reflects_activity(client, auth_headers):
    advisor = auth_headers("advisor")
    director = auth_headers("director")
    _create_suspicious_alert(client, advisor)

    kpi = client.get("/analytics/kpi", headers=director).json()

    assert kpi["total_clients"] == 1
    assert kpi["total_accounts"] == 1
    assert kpi["total_transactions"] == 6
    assert kpi["open_alerts"] == 1
    assert float(kpi["total_deposits"]) == 750.0       # 5 x 150
    assert float(kpi["total_withdrawals"]) == 40000.0
    assert kpi["average_risk_score"] is not None


def test_trends_and_distribution(client, auth_headers):
    advisor = auth_headers("advisor")
    director = auth_headers("director")
    _create_suspicious_alert(client, advisor)

    trends = client.get("/analytics/trends", headers=director).json()
    assert len(trends) == 1  # toute l'activité du test est aujourd'hui
    assert trends[0]["transaction_count"] == 6

    distribution = client.get("/analytics/distribution", headers=director).json()
    types = {row["transaction_type"]: row["count"] for row in distribution}
    assert types == {"deposit": 5, "withdrawal": 1}
