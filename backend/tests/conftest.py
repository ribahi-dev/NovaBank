"""conftest.py — infrastructure de test partagée.

Stratégie d'isolation (pattern standard en entreprise) :
  - une base DÉDIÉE novabank_test (jamais la base de dev) créée à la volée ;
  - schéma recréé une fois par session de test (drop_all + create_all) ;
  - chaque test s'exécute dans une TRANSACTION ANNULÉE à la fin
    (join_transaction_mode="create_savepoint" : les commit() du code
    applicatif ne libèrent que des savepoints, le rollback final efface
    tout) -> les tests sont indépendants et rapides, sans TRUNCATE.
"""

import os

# Défaut AVANT tout import de `app` (en CI comme en local, un vrai
# DATABASE_URL d'environnement garde la priorité).
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5433/novabank"
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import models  # noqa: E402,F401  (enregistre les tables dans Base.metadata)
from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB_NAME = "novabank_test"
TEST_PASSWORD = "Password123!"


@pytest.fixture(scope="session")
def engine():
    url = make_url(settings.database_url)

    # Création de la base de test si absente (connexion à la base de
    # maintenance "postgres" en AUTOCOMMIT : CREATE DATABASE refuse de
    # s'exécuter dans une transaction).
    admin_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin_engine.dispose()

    test_engine = create_engine(url.set(database=TEST_DB_NAME))
    Base.metadata.drop_all(test_engine)   # schéma toujours propre, même après un crash
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture()
def db(engine):
    connection = engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    outer.rollback()  # efface TOUT ce que le test a écrit, commits inclus
    connection.close()


@pytest.fixture()
def client(db):
    # L'API utilise LA session du test : ce que le test prépare en base,
    # l'endpoint le voit, et tout disparaît au rollback final.
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    """Fabrique d'utilisateurs : make_user('director') -> User persisté."""

    def _make(role: str = "advisor", email: str | None = None, is_active: bool = True):
        user = models.User(
            first_name="Test",
            last_name=role.capitalize(),
            email=email or f"{role}@novabank.ma",
            password_hash=hash_password(TEST_PASSWORD),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers(client, make_user):
    """Fabrique d'en-têtes : auth_headers('advisor') -> {'Authorization': ...}.

    Email unique à CHAQUE appel (compteur) : un même test peut demander
    plusieurs fois le même rôle sans violer l'unicité de users.email.
    """
    counter = iter(range(1, 1000))

    def _headers(role: str = "advisor"):
        user = make_user(role=role, email=f"{role}+auth{next(counter)}@novabank.ma")
        response = client.post(
            "/auth/login", data={"username": user.email, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _headers
