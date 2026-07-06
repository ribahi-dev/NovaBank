# NovaBank — Plateforme bancaire intelligente d'aide à la décision

Prototype (MVP) de plateforme web pour une agence bancaire : gestion des
clients, comptes et transactions, **scoring de risque par IA avec
explication lisible**, centre d'alertes, dashboard analytique et
mécanismes de cybersécurité (JWT, RBAC, journal d'audit).

## Le scénario central

1. Un **conseiller** saisit une transaction.
2. Le backend l'enregistre et le module **IA** calcule un score de risque (0–100).
3. Si le score dépasse le seuil, une **alerte** est créée avec une explication
   ("montant 3,2× supérieur aux habitudes du client ; heure inhabituelle...").
4. Le **directeur d'agence** consulte l'alerte dans le dashboard, la qualifie
   et la clôture — chaque action est tracée dans le journal d'audit.

## Stack

| Couche | Technologie |
|---|---|
| Frontend | React |
| Backend | FastAPI (Python) |
| Base de données | PostgreSQL 16 |
| ORM / migrations | SQLAlchemy 2.0 / Alembic |
| IA | scikit-learn (Isolation Forest / Random Forest) |
| Sécurité | JWT, bcrypt, RBAC, audit |
| Conteneurisation | Docker Compose |

## Démarrage

```bash
cp .env.example .env          # variables Docker (mot de passe PostgreSQL)
docker compose up -d          # démarre PostgreSQL
```

Puis voir [backend/README.md](backend/README.md) pour lancer l'API.

## Documentation

- [Plan directeur](docs/plan_directeur.md) — vision finale et étapes de réalisation
- [Base de données](docs/base_de_donnees.md) — modèle de données du MVP
- [Schéma cible](docs/schema_cible.sql) — architecture PostgreSQL "grande échelle"
  (partitionnement, RLS, triggers d'audit) documentée pour l'évolution

## Équipe

Projet de stage (2 mois) — El Mehdi Ribahi · Adam El Mansour · Malak Harf-ezzine
Encadrante : Raiss Bouchra
