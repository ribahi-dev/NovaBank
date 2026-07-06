"""Premier test du projet : l'API démarre et répond.

Pourquoi commencer par un test aussi simple :
    1. Il valide toute la chaîne d'assemblage (config chargée, app FastAPI
       construite, routing opérationnel) sans dépendre de PostgreSQL.
    2. Il donne à la CI quelque chose à exécuter dès le premier jour :
       le badge vert existe AVANT le code compliqué, et chaque commit
       suivant est vérifié automatiquement.

TestClient : un client HTTP qui appelle l'application EN MÉMOIRE (aucun
serveur uvicorn, aucun réseau) — les tests restent rapides et fiables.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    # Deux assertions : le contrat HTTP (status code) ET le contenu.
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
