"""Tests CRUD clients : création, recherche, mise à jour, désactivation."""

VALID_CLIENT = {
    "first_name": "Amina",
    "last_name": "Benali",
    "cin": "AB123456",
    "phone": "0661234567",
    "profession": "Enseignante",
    "monthly_income": "8500.50",
}


def test_create_and_get_client(client, auth_headers):
    headers = auth_headers("advisor")

    created = client.post("/clients", headers=headers, json=VALID_CLIENT)
    assert created.status_code == 201
    client_id = created.json()["id"]

    fetched = client.get(f"/clients/{client_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["cin"] == "AB123456"
    assert fetched.json()["is_active"] is True


def test_duplicate_cin_rejected(client, auth_headers):
    headers = auth_headers("advisor")
    assert client.post("/clients", headers=headers, json=VALID_CLIENT).status_code == 201
    assert client.post("/clients", headers=headers, json=VALID_CLIENT).status_code == 409


def test_search_by_name_and_cin(client, auth_headers):
    headers = auth_headers("advisor")
    client.post("/clients", headers=headers, json=VALID_CLIENT)
    client.post(
        "/clients", headers=headers,
        json={**VALID_CLIENT, "cin": "CD789012", "first_name": "Karim", "last_name": "Alaoui"},
    )

    by_name = client.get("/clients", headers=headers, params={"search": "benali"}).json()
    assert len(by_name) == 1 and by_name[0]["last_name"] == "Benali"

    by_cin = client.get("/clients", headers=headers, params={"search": "CD789"}).json()
    assert len(by_cin) == 1 and by_cin[0]["first_name"] == "Karim"


def test_patch_updates_only_sent_fields(client, auth_headers):
    headers = auth_headers("advisor")
    client_id = client.post("/clients", headers=headers, json=VALID_CLIENT).json()["id"]

    patched = client.patch(f"/clients/{client_id}", headers=headers, json={"phone": "0700000000"})

    assert patched.status_code == 200
    assert patched.json()["phone"] == "0700000000"
    assert patched.json()["first_name"] == "Amina"  # inchangé


def test_delete_is_soft_and_hides_from_list(client, auth_headers):
    headers = auth_headers("advisor")
    client_id = client.post("/clients", headers=headers, json=VALID_CLIENT).json()["id"]

    assert client.delete(f"/clients/{client_id}", headers=headers).status_code == 204

    # Absent de la liste par défaut, mais toujours accessible directement
    # (suppression logique : l'historique reste consultable).
    assert client.get("/clients", headers=headers).json() == []
    still_there = client.get(f"/clients/{client_id}", headers=headers)
    assert still_there.status_code == 200
    assert still_there.json()["is_active"] is False


def test_invalid_payload_is_422(client, auth_headers):
    headers = auth_headers("advisor")
    response = client.post(
        "/clients", headers=headers, json={**VALID_CLIENT, "cin": "123", "monthly_income": "-5"}
    )
    assert response.status_code == 422
    fields = {err["loc"][-1] for err in response.json()["detail"]}
    assert {"cin", "monthly_income"} <= fields  # les DEUX erreurs sont signalées
