<div align="center">

# 🏦 NovaBank — Plateforme bancaire intelligente d'aide à la décision

**Plateforme web pour agence bancaire** : gestion des clients, comptes et transactions,
**détection d'anomalies par Machine Learning (Random Forest) avec explication lisible**,
boucle de feedback, centre d'alertes, tableau de bord analytique et cybersécurité
(JWT, RBAC, audit).

> 🎓 **Version PFE** — cette version enrichit le MVP d'un véritable modèle de Machine
> Learning entraîné et évalué, d'une boucle de feedback humain et de migrations Alembic.

Projet de stage — El Mehdi Ribahi · Adam El Mansour · Malak Harf-ezzine
Encadrante : Raiss Bouchra

</div>

---

## 🚀 Démarrage en 1 clic (le plus simple)

> **Prérequis unique : [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé.**
> Rien d'autre à installer (ni Python, ni Node, ni PostgreSQL).

| Système | Comment lancer |
|---|---|
| **Windows** | Double-cliquer sur **`demarrer.bat`** |
| **macOS / Linux** | Exécuter **`./demarrer.sh`** dans un terminal |
| **N'importe où** | Taper **`docker compose up -d --build`** |

Le script construit et démarre **toute la plateforme** (base de données + backend +
frontend), crée les tables et injecte les données de démonstration **automatiquement**.

Au bout de ~1 minute (2–4 min la première fois), l'application est prête :

| Adresse | Contenu |
|---|---|
| 👉 **http://localhost:8090** | **L'application** (interface web) |
| http://localhost:8000/docs | Documentation interactive de l'API (Swagger) |

### 🔑 Comptes de démonstration

| Rôle | Email | Mot de passe |
|---|---|---|
| Directeur d'agence | `directeur@novabank.ma` | `Directeur@2026!` |
| Conseiller bancaire | `conseiller@novabank.ma` | `Conseiller@2026!` |
| Administrateur | `admin@novabank.ma` | `Admin@2026!` |

**Pour arrêter** : double-clic sur `arreter.bat` (Windows) ou `docker compose down`.

---

## 🎬 Le scénario démontré

```
  Conseiller saisit une transaction
          │
          ▼
  Le backend l'enregistre (verrou anti-corruption des soldes)
          │
          ▼
  Le moteur de risque calcule un score 0–100 + une explication lisible
          │
          ▼
  Si le score dépasse le seuil → une ALERTE est créée automatiquement
          │
          ▼
  Le directeur voit l'alerte sur son dashboard, lit l'explication,
  la qualifie et la clôture  →  tout est tracé dans le journal d'audit
```

**Exemple d'explication produite** : *« Signaux détectés : montant 3,2× supérieur au
revenu mensuel du client ; opération nocturne, hors des horaires habituels ; ville
inhabituelle. »*

---

## 🧱 Architecture

```
┌────────────────────┐   HTTP    ┌──────────────────────────┐   SQL   ┌──────────────┐
│   Frontend React   │  + JWT    │      Backend FastAPI     │ ──────► │  PostgreSQL  │
│  (nginx, port 8090)│ ────────► │      (port 8000)         │         │  (port 5433) │
│                    │  /api/... │                          │         │              │
│  Login, Dashboard, │           │  routers  (HTTP)         │         │  7 tables    │
│  Clients, Comptes, │           │  services (métier)       │         │  contraintes │
│  Transactions,     │           │  schemas  (Pydantic)     │         │  index       │
│  Fraude, Rapports… │           │  models   (SQLAlchemy)   │         │              │
└────────────────────┘           └──────────────────────────┘         └──────────────┘
        │                                     │                              │
        └─────────────────────────────────────┴──────────────────────────────┘
                    Tout est orchestré par Docker Compose
```

**Architecture en couches** (`routers → services → models`) : un router ne touche jamais
la base directement, un service ne connaît jamais HTTP. C'est ce qui rend le code
testable et évolutif.

---

## 🛠️ Stack technique

| Couche | Technologie | Pourquoi |
|---|---|---|
| Frontend | React 18 + **TypeScript** + Vite | Typage fort, écosystème riche, build rapide |
| UI | Tailwind CSS + Framer Motion | Design premium, mode sombre, animations |
| Backend | **FastAPI** (Python) | Performant, validation Pydantic, Swagger auto |
| ORM | **SQLAlchemy 2.0** | Modèles Python ↔ tables PostgreSQL |
| Base | **PostgreSQL 16** | SGBD relationnel robuste, standard entreprise |
| IA | **scikit-learn (Random Forest)** | Scoring de risque entraîné + évalué, repli sur règles |
| Migrations | **Alembic** | Versionnage du schéma de la base |
| Sécurité | **JWT + bcrypt + RBAC** | Auth stateless, rôles vérifiés côté serveur |
| Conteneurs | **Docker Compose** | Déploiement reproductible en une commande |
| Tests / CI | **pytest + GitHub Actions** | 44 tests d'intégration, badge vert à chaque push |

---

## ✨ Fonctionnalités (10 modules du cahier des charges)

- 🔐 **Authentification & rôles** — JWT, 3 rôles (Admin / Directeur / Conseiller),
  verrouillage anti force-brute après 5 échecs, refresh token.
- 👥 **Clients** — création, recherche (nom/CIN), fiche complète, désactivation logique.
- 💳 **Comptes** — ouverture, numéro généré par le système, blocage/déblocage.
- 🔁 **Transactions** — dépôt, retrait, **virement avec verrou PostgreSQL** (pas de
  corruption de solde en cas d'opérations simultanées).
- 🤖 **Scoring de risque par IA** — modèle **Random Forest** (scikit-learn) sur 5 signaux
  (montant/revenu, heure, ville, fréquence), score 0–100 **avec explication lisible**.
  Repli automatique sur un moteur de règles si le modèle est absent.
- 🔁 **Boucle de feedback** — la qualification des alertes par le directeur
  (fraude confirmée / faux positif) alimente le réentraînement du modèle.
- 🚨 **Centre d'alertes** — création automatique, cycle de vie (ouverte → en cours →
  clôturée), détail explicable.
- 📊 **Tableau de bord** — KPI et graphiques Plotly (activité, répartition, risque).
- 📄 **Rapports** — export des données (CSV/Excel).
- 📜 **Audit** — journal append-only de toutes les actions sensibles (qui, quoi, quand, IP).
- 🌗 **Interface premium** — mode clair/sombre, responsive, glassmorphism.

---

## 👩‍💻 Développement (sans Docker)

Pour développer avec rechargement à chaud (modifier le code sans reconstruire) :

<details>
<summary><b>Backend</b> (Python 3.14)</summary>

```bash
docker compose up -d postgres     # juste la base
cd backend
python -m venv venv
venv\Scripts\activate             # Windows  (source venv/bin/activate sur macOS/Linux)
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env            # puis adapter si besoin
python -m scripts.create_tables   # crée les tables
python -m scripts.seed            # données de démo
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

Tests : `pytest -v`  ·  Lint : `ruff check .`
</details>

<details>
<summary><b>Frontend</b> (Node 22)</summary>

```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```
</details>

---

## 📚 Documentation

| Document | Contenu |
|---|---|
| [docs/GUIDE_COMPLET.md](docs/GUIDE_COMPLET.md) | Guide fichier par fichier + questions du jury |
| [docs/evaluation_ml.md](docs/evaluation_ml.md) | Méthodologie et métriques du module IA (version PFE) |
| [docs/plan_directeur.md](docs/plan_directeur.md) | Vision finale et étapes de réalisation |
| [docs/base_de_donnees.md](docs/base_de_donnees.md) | Modèle de données du MVP |
| [docs/schema_cible.sql](docs/schema_cible.sql) | Architecture PostgreSQL « grande échelle » (partitionnement, RLS, triggers) documentée pour l'évolution |

Chaque fichier de code contient un en-tête expliquant **son rôle, le problème qu'il
résout et les choix techniques** — la documentation vit dans le code.

---

## ⚠️ Périmètre

Prototype pédagogique sur **données simulées et anonymisées**. Aucune connexion à un
système bancaire réel, aucun mouvement d'argent réel. Environnement de démonstration
local (Docker).
