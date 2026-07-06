"""Crée toutes les tables dans PostgreSQL à partir des modèles SQLAlchemy.

⚠️ Outil TEMPORAIRE de la phase de mise en place (sera remplacé par Alembic
en Phase B7 du plan directeur). Différence fondamentale :
  - create_all() : crée les tables MANQUANTES, mais ne modifie JAMAIS une
    table existante (ajouter une colonne ? il ne fait rien, silencieusement).
  - Alembic : versionne chaque évolution du schéma (upgrade/downgrade),
    comme git versionne le code. C'est pour ça qu'aucune entreprise ne
    gère son schéma avec create_all().

Usage (depuis backend/, venv activé, PostgreSQL démarré) :
    python -m scripts.create_tables
"""

from app.db.base import Base
from app.db.session import engine

# Import indispensable même s'il semble "inutilisé" : c'est lui qui charge
# les classes modèles et remplit Base.metadata (voir app/models/__init__.py).
# `noqa: F401` dit au linter ruff de ne pas le signaler comme import mort.
from app import models  # noqa: F401


def main():
    # Parcourt Base.metadata et exécute les CREATE TABLE IF NOT EXISTS
    # dans l'ordre des dépendances (clients avant accounts, etc. —
    # SQLAlchemy trie les clés étrangères automatiquement).
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès dans la base :", engine.url.database)


if __name__ == "__main__":
    main()
