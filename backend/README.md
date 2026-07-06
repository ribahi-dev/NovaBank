# Backend — API NovaBank

Ce dossier contient l'API FastAPI et la couche base de données du projet.

## Démarrage rapide

```bash
# 1. PostgreSQL (depuis la racine du projet)
docker compose up -d

# 2. Environnement Python
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

# 3. Configuration : copier .env.example en .env et adapter si besoin

# 4. Créer les tables (temporaire — remplacé par Alembic en Phase B7)
python -m scripts.create_tables

# 5. Lancer l'API
uvicorn app.main:app --reload
# Swagger : http://localhost:8000/docs
```

## Vérifications

```bash
pytest -v          # tests
ruff check .       # lint
```

## Architecture (couches, du haut vers le bas)

| Dossier | Rôle | Règle |
|---|---|---|
| `app/routers/` | endpoints HTTP (à venir) | ne touche jamais la base directement |
| `app/services/` | logique métier (à venir) | ne connaît pas HTTP |
| `app/repositories/` | accès données (à venir) | seul à manipuler les Sessions |
| `app/schemas/` | validation Pydantic (à venir) | contrat d'entrée/sortie de l'API |
| `app/models/` | tables SQLAlchemy | source de vérité du schéma |
| `app/core/` | configuration, sécurité | transverse |
| `app/db/` | Engine, Session, Base | unique point de contact PostgreSQL |

## Entités du domaine

- `User` : utilisateur de la plateforme (conseiller, directeur, admin)
- `Client` : client bancaire simulé
- `Account` : compte bancaire rattaché à un client
- `Transaction` : dépôt, retrait ou virement
- `RiskScore` : score IA (0–100) + explication, lié 1-1 à une transaction
- `Alert` : alerte levée si le score dépasse le seuil, traitée par le directeur
- `AuditLog` : journal d'audit append-only (qui a fait quoi, quand, d'où)

Chaque fichier du projet contient un en-tête expliquant son rôle,
les problèmes qu'il résout et les choix techniques — les lire fait
partie de la documentation du projet.
