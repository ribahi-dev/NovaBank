# 🛠️ Guide de construction pas à pas — NovaBank (de zéro à la PFE)

> **Objectif de ce guide** : t'apprendre à **reconstruire tout le projet toi-même**, dans
> l'ordre, en comprenant chaque étape, chaque fichier et chaque commande. C'est le mode
> d'emploi complet — de l'installation des outils jusqu'à la version PFE avec IA.
>
> **Comment l'utiliser** : suis les parties dans l'ordre. Chaque partie explique
> **POURQUOI** on la fait, **QUELS fichiers** on crée, **QUELLES commandes** on tape, et
> **COMMENT vérifier** que ça marche avant de continuer.

## Plan
- [Partie 0 — Préparer sa machine](#p0)
- [Partie 1 — Concevoir la base de données](#p1)
- [Partie 2 — Fondations du backend](#p2)
- [Partie 3 — PostgreSQL avec Docker](#p3)
- [Partie 4 — Les modèles SQLAlchemy](#p4)
- [Partie 5 — Les schémas Pydantic](#p5)
- [Partie 6 — La sécurité (JWT, bcrypt, RBAC)](#p6)
- [Partie 7 — Les services (logique métier)](#p7)
- [Partie 8 — Les routers (API REST)](#p8)
- [Partie 9 — Les tests + l'intégration continue](#p9)
- [Partie 10 — Le module IA (Random Forest + SHAP)](#p10)
- [Partie 11 — Les rapports serveur (PDF/Excel)](#p11)
- [Partie 12 — Le frontend React](#p12)
- [Partie 13 — La dockerisation complète (1 clic)](#p13)
- [Partie 14 — Les migrations Alembic](#p14)
- [Ordre de travail recommandé](#ordre)

---

<a name="p0"></a>
## Partie 0 — Préparer sa machine

**Pourquoi** : avant de coder, il faut les bons outils. On les installe une fois.

### Outils à installer

| Outil | Rôle | Vérifier avec |
|---|---|---|
| **Python 3.14** | langage du backend | `python --version` |
| **Node.js 22** | outils du frontend | `node --version` |
| **Docker Desktop** | conteneurs (base + déploiement) | `docker --version` |
| **Git** | versionner le code | `git --version` |
| **VSCode** | éditeur de code | — |

> Chaque commande de vérification doit afficher un numéro de version. Sinon, l'outil n'est
> pas installé ou pas dans le PATH.

### Créer le projet

```bash
mkdir NovaBank && cd NovaBank
git init                       # initialise le suivi de version
```

Structure de départ à créer :
```
NovaBank/
├── backend/       (l'API)
├── frontend/      (l'interface)
└── docs/          (la documentation)
```

**Vérification** : `git status` doit répondre « On branch main / master ».

---

<a name="p1"></a>
## Partie 1 — Concevoir la base de données

**Pourquoi** : on ne code jamais avant d'avoir réfléchi aux données. On liste ce que le
système doit mémoriser.

**Réflexion** : une agence bancaire manipule des **clients** qui possèdent des **comptes**,
sur lesquels ont lieu des **transactions**. Chaque transaction reçoit un **score de risque**
qui peut créer une **alerte**. Des **utilisateurs** (employés) se connectent, et chaque
action est tracée dans un **journal d'audit**.

On obtient **7 entités** et leurs relations :
```
Client 1──N Compte 1──N Transaction 1──1 ScoreRisque
                              └──N Alerte
Utilisateur 1──N Transaction (l'auteur)
Utilisateur 1──N JournalAudit
```

**Livrable de cette partie** : un schéma sur papier (ou un diagramme). Pas encore de code.
On documente ce raisonnement dans `docs/base_de_donnees.md`.

---

<a name="p2"></a>
## Partie 2 — Fondations du backend

**Pourquoi** : mettre en place l'environnement Python isolé et la connexion à la base.

### 2.1 — Environnement virtuel et dépendances

```bash
cd backend
python -m venv venv                 # crée un environnement Python isolé
venv\Scripts\activate               # l'active (Windows). macOS/Linux : source venv/bin/activate
```

> **Pourquoi un venv ?** Pour que les dépendances du projet n'entrent pas en conflit avec
> celles d'autres projets sur la machine.

Créer `backend/requirements.txt` avec les versions **figées** :
```
fastapi==0.139.0
uvicorn[standard]==0.50.2
sqlalchemy==2.0.51
psycopg[binary]==3.3.4
pydantic==2.13.4
pydantic-settings==2.14.2
pyjwt==2.13.0
pwdlib[bcrypt]==0.3.0
python-multipart==0.0.32
```
Puis : `pip install -r requirements.txt`

> **Pourquoi figer les versions (`==`) ?** Pour que toute l'équipe et le serveur installent
> exactement la même chose — sinon « ça marche chez moi » mais pas ailleurs.

### 2.2 — La configuration (`app/core/config.py`)

**Rôle** : lire les réglages (URL de la base, clé secrète) depuis un fichier `.env`, et les
**valider** au démarrage.

**Concept clé** : on **sépare le code de la configuration** (principe *12-factor*). Les
secrets ne sont JAMAIS écrits dans le code versionné. On crée un `.env.example` (modèle,
versionné) et chacun copie en `.env` (réel, ignoré par git via `.gitignore`).

### 2.3 — La connexion à la base (`app/db/`)

Deux fichiers :
- **`base.py`** : définit `Base`, la classe mère de tous les modèles.
- **`session.py`** : crée l'**Engine** (moteur + pool de connexions) et la fonction
  `get_db()` qui fournit une **session par requête**.

**Concept clé** : une **session** = l'espace de travail d'une requête (elle suit les objets,
accumule les changements, les envoie au `commit`). Chaque requête HTTP a la sienne, fermée à
la fin quoi qu'il arrive.

**Vérification** : rien de visible encore ; on teste au bout de la partie 4.

---

<a name="p3"></a>
## Partie 3 — PostgreSQL avec Docker

**Pourquoi** : au lieu d'installer PostgreSQL « en dur », on le lance dans un conteneur
Docker — propre, jetable, identique sur toutes les machines.

Créer `docker-compose.yml` (à la racine) avec un service `postgres`. Points importants :
- image `postgres:16` (version figée) ;
- mot de passe via variable d'environnement (pas en dur) ;
- **port hôte 5433** (car un PostgreSQL déjà installé occupe souvent 5432) ;
- un **volume** pour que les données survivent au redémarrage ;
- un **healthcheck** (`pg_isready`).

```bash
docker compose up -d postgres       # démarre la base en arrière-plan
docker compose ps                   # doit montrer "healthy"
```

**Vérification** : `docker compose ps` affiche le conteneur `postgres` en `healthy`.

---

<a name="p4"></a>
## Partie 4 — Les modèles SQLAlchemy

**Pourquoi** : traduire les 7 entités (partie 1) en classes Python. SQLAlchemy transformera
ces classes en tables SQL. **Ces modèles sont la source de vérité du schéma.**

On crée un fichier par entité dans `app/models/` : `user.py`, `client.py`, `account.py`,
`transaction.py`, `risk_score.py`, `alert.py`, `audit_log.py`.

**Modèle type** (`client.py`) — anatomie :
```python
class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    cin: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    monthly_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    accounts = relationship("Account", back_populates="client")
```

**Concepts clés à retenir** :
- `Mapped[str]` = NOT NULL ; `Mapped[str | None]` = nullable.
- Argent = `Numeric` (décimal exact), **jamais `Float`** (arrondis).
- `server_default=func.now()` = c'est **PostgreSQL** qui horodate (une seule horloge).
- `relationship(...)` = navigation objet (client.accounts) ; la clé étrangère vit côté enfant.

On regroupe tout dans `app/models/__init__.py` (importer un modèle = enregistrer sa table).

### Créer les tables

Créer `scripts/create_tables.py` qui appelle `Base.metadata.create_all(engine)`, puis :
```bash
python -m scripts.create_tables
```

**Vérification** :
```bash
docker exec <conteneur_postgres> psql -U postgres -d novabank -c "\dt"
```
→ doit lister les 7 tables.

---

<a name="p5"></a>
## Partie 5 — Les schémas Pydantic

**Pourquoi** : les modèles décrivent la **base** ; les schémas Pydantic décrivent ce que
l'**API accepte et renvoie**. On ne renvoie JAMAIS un modèle directement (sécurité,
découplage, validation — voir GUIDE_COMPLET §4.4).

Pour chaque entité, on crée dans `app/schemas/` trois variantes :
- `...Create` : les champs à fournir à la création (sans `id`, sans champs système) ;
- `...Update` : tous optionnels (modification partielle) ;
- `...Response` : ce qu'on renvoie (avec `id`, `created_at`).

**Concept clé** : `model_config = ConfigDict(from_attributes=True)` sur les `Response`
permet de convertir un objet SQLAlchemy en JSON automatiquement.

---

<a name="p6"></a>
## Partie 6 — La sécurité (JWT, bcrypt, RBAC)

**Pourquoi** : une banque doit sécuriser l'accès. On met en place l'authentification et
l'autorisation.

### 6.1 — `app/core/security.py`
- **`hash_password` / `verify_password`** (bcrypt) : on ne stocke jamais le mot de passe,
  seulement son hachage à sens unique.
- **`create_access_token` / `create_refresh_token` / `decode_token`** (JWT) : un jeton signé
  remis à la connexion, vérifié à chaque requête. On rejette l'algorithme `none` (attaque
  classique) et on distingue access / refresh par un champ `type`.

### 6.2 — `app/core/deps.py`
- **`get_current_user`** : lit le jeton, vérifie, charge l'utilisateur.
- **`require_role("admin", ...)`** : la **dépendance RBAC**. 401 = pas authentifié ;
  403 = authentifié mais pas le bon rôle.

**Concept clé** : l'**autorisation est vérifiée côté serveur à chaque requête**. Un menu
caché côté frontend n'est PAS une sécurité.

---

<a name="p7"></a>
## Partie 7 — Les services (logique métier)

**Pourquoi** : la logique métier ne doit pas être dans les routers (couche HTTP). On la met
dans `app/services/`. **Un service ne connaît jamais HTTP.**

Fichiers :
- **`auth_service.py`** : connexion, verrouillage après 5 échecs, journalisation.
- **`transaction_service.py`** : dépôt/retrait/virement. ⭐ **Le point technique fort** :
  ```python
  account = db.get(Account, id, with_for_update=True)  # SELECT ... FOR UPDATE
  ```
  Ce **verrou** garantit que deux virements simultanés ne corrompent pas le solde (ACID).
- **`scoring_service.py`** : calcule le score de risque (voir partie 10).
- **`audit_service.py`** : écrit dans le journal (append-only).

---

<a name="p8"></a>
## Partie 8 — Les routers (API REST)

**Pourquoi** : exposer les fonctionnalités en endpoints HTTP. Un router **valide → délègue
au service → renvoie une réponse HTTP**.

On crée dans `app/routers/` : `auth.py`, `users.py`, `clients.py`, `accounts.py`,
`transactions.py`, `alerts.py`, `analytics.py`, `audit.py`, puis on les branche dans
`app/main.py` (`app.include_router(...)`).

**Lancer l'API** :
```bash
uvicorn app.main:app --reload
```
**Vérification** : ouvrir `http://localhost:8000/docs` (Swagger). On voit tous les endpoints
et on peut les tester à la main.

**Concept clé — les codes HTTP** : 200 OK, 201 créé, 400 refus métier, 401 non authentifié,
403 non autorisé, 404 introuvable, 409 conflit, 422 données invalides.

---

<a name="p9"></a>
## Partie 9 — Les tests + l'intégration continue

**Pourquoi** : prouver que tout marche, automatiquement, à chaque modification.

### 9.1 — Tests (pytest)
- Ajouter `requirements-dev.txt` (pytest, httpx, ruff) et `pytest.ini` (`pythonpath = .`).
- Créer `tests/conftest.py` : base de test isolée, chaque test dans une transaction annulée.
- Écrire des tests par domaine (`test_auth.py`, `test_transactions_api.py`, ...), **dont des
  tests d'échec** (mauvais mot de passe, solde insuffisant, accès refusé).

```bash
pytest -v          # lance les tests
ruff check .       # vérifie le style
```

### 9.2 — Intégration continue (`.github/workflows/ci.yml`)

Un fichier qui dit à GitHub : à chaque `push`, installe, lint et lance les tests sur une
machine neuve avec un PostgreSQL éphémère. **Le badge vert prouve la santé du projet.**

**Piège fréquent** : la CI lance `pytest` (pas `python -m pytest`), qui n'ajoute pas le
dossier courant au chemin Python → il faut `pythonpath = .` dans `pytest.ini`.

---

<a name="p10"></a>
## Partie 10 — Le module IA (Random Forest + SHAP) — version PFE

**Pourquoi** : remplacer le moteur de règles par un vrai modèle de Machine Learning, évalué
et explicable.

### 10.1 — Les features (`app/ml/features.py`)
Transformer une transaction en 5 nombres (montant/revenu, montant/moyenne, nuit, ville,
fréquence). **Code partagé entre l'entraînement et l'inférence** (sinon *training/serving
skew*).

### 10.2 — L'entraînement (`scripts/train_model.py`)
- Générer un jeu simulé **avec chevauchement volontaire** des classes (sinon métriques
  fausses).
- Entraîner un **Random Forest**, le comparer à un **Isolation Forest** et à la **baseline
  de règles**.
- Évaluer avec **précision / rappel / F1 / AUC-PR** (jamais l'accuracy seule).
- Sauver l'artefact `ml_artifacts/model.joblib`.

```bash
pip install numpy scikit-learn joblib
python -m scripts.train_model
```

### 10.3 — Le double moteur (`app/ml/model.py` + `scoring_service.py`)
Le scoring utilise le **modèle ML si l'artefact existe**, sinon **repli sur les règles**.
Chaque score garde la trace du moteur (`model_version`).

### 10.4 — L'explicabilité SHAP (`app/ml/model.py::explain_shap`)
```bash
pip install shap numba==0.66.0 llvmlite==0.48.0   # numba exige numpy<2.5
```
`shap.TreeExplainer` donne la contribution de chaque variable au score. On la stocke
(`risk_scores.shap_values`, JSON) et on l'affiche dans le frontend (barres).

> **Piège vécu** : `numba` (dépendance de SHAP) exige `numpy<2.5`. Il faut donc épingler
> `numpy==2.4.6`. Sans ce pin, le build Docker échoue sur un conflit de versions.

### 10.5 — La boucle de feedback ⭐
Quand le directeur clôture une alerte, il la **qualifie** (fraude / faux positif). Ces
qualifications (`alerts.resolution`) deviennent des **étiquettes d'entraînement**
(`load_feedback_labels`). Le système apprend de l'agence.

---

<a name="p11"></a>
## Partie 11 — Les rapports serveur (PDF/Excel)

**Pourquoi** : le directeur doit exporter des rapports (Module 10 du cahier des charges).

```bash
pip install reportlab openpyxl
```
- **`app/services/report_service.py`** : `generate_activity_pdf` (reportlab) et
  `generate_transactions_xlsx` (openpyxl) → renvoient des `bytes`.
- **`app/routers/reports.py`** : endpoints qui servent ces fichiers en téléchargement
  (`StreamingResponse` + bon type MIME), réservés directeur/admin.

**Vérification** :
```bash
curl -s http://localhost:8000/reports/activity.pdf -H "Authorization: Bearer <token>" -o r.pdf
file r.pdf     # -> "PDF document"
```

---

<a name="p12"></a>
## Partie 12 — Le frontend React

**Pourquoi** : l'interface que voient les utilisateurs.

### 12.1 — Mise en place
```bash
cd frontend
npm create vite@latest . -- --template react-ts   # React + TypeScript
npm install axios react-router-dom framer-motion lucide-react
npm install -D tailwindcss @tailwindcss/vite
```
Fichiers de config : `vite.config.ts` (avec un **proxy** `/api` → backend, pour éviter les
problèmes CORS en dev), `tsconfig.json`, `src/styles/index.css` (le système de design :
couleurs, thème clair/sombre).

### 12.2 — L'architecture (dossiers `src/`)
- **`api/`** : `client.ts` (axios + jeton JWT + refresh auto), `types.ts` (types miroir de
  l'API).
- **`contexts/`** : `AuthContext` (qui est connecté), `ThemeContext` (clair/sombre),
  `ToastContext` (notifications).
- **`components/ui/`** : briques réutilisables (Button, Card, Input, Table, Dialog...).
- **`components/layout/`** : Sidebar (menu par rôle), Navbar, AppLayout.
- **`pages/`** : un fichier par écran (Login, Dashboard, Clients, NewTransaction, Fraud...).
- **`App.tsx`** : le routage, avec gardes de rôle.

```bash
npm run dev        # http://localhost:5173
```

**Concept clé** : le rôle de l'utilisateur pilote le menu ET les routes accessibles. (Mais
la vraie sécurité reste le RBAC serveur.)

---

<a name="p13"></a>
## Partie 13 — La dockerisation complète (démarrage 1 clic)

**Pourquoi** : qu'un collègue lance TOUT (base + API + frontend) en une commande.

Fichiers :
- **`backend/Dockerfile`** : construit l'image de l'API (image slim, dépendances en cache,
  utilisateur non-root, **entraînement du modèle au build**).
- **`frontend/Dockerfile`** : build React en 2 étapes (Node compile → nginx sert).
- **`frontend/nginx.conf`** : sert l'app et relaie `/api` vers le backend.
- **`backend/scripts/docker_entrypoint.py`** : au démarrage, attend la base, crée les
  tables, injecte les données de démo, puis lance le serveur.
- **`docker-compose.yml`** : les 3 services (postgres + api + frontend).
- **`demarrer.bat` / `demarrer.sh`** : lancement en 1 clic.

> **Piège vécu 1** : ne PAS mettre de `container_name` fixe → sinon conflit « name already
> in use » entre deux dossiers/essais.
>
> **Piège vécu 2** : les `.bat` doivent être en fins de ligne **CRLF** (voir `.gitattributes`)
> et n'utiliser que des labels au niveau supérieur (pas de `goto` dans un bloc `( )`).

```bash
docker compose up -d --build     # construit et lance tout
# -> application sur http://localhost:8090
```

---

<a name="p14"></a>
## Partie 14 — Les migrations Alembic

**Pourquoi** : `create_tables` crée les tables manquantes mais ne sait pas **modifier** une
table existante (ajouter une colonne). Alembic **versionne** chaque évolution du schéma.

```bash
pip install alembic
alembic init alembic                 # crée le dossier de migrations
# (configurer alembic/env.py : URL depuis config, target_metadata = Base.metadata)
alembic revision --autogenerate -m "baseline"   # génère une migration
alembic upgrade head                 # l'applique
```

Exemple concret du projet : quand on a ajouté la colonne `shap_values`, on a créé une
migration qui fait `op.add_column("risk_scores", ...)`.

---

<a name="ordre"></a>
## Ordre de travail recommandé (résumé)

```
0. Installer les outils
1. Concevoir la base (papier)
2. Backend : venv + config + connexion
3. Docker PostgreSQL
4. Modèles SQLAlchemy → créer les tables
5. Schémas Pydantic
6. Sécurité (JWT, bcrypt, RBAC)
7. Services (dont le virement avec verrou)
8. Routers → tester dans Swagger
9. Tests + CI (badge vert)
────────── à ce stade : PFA fonctionnelle ──────────
10. Module IA (Random Forest + SHAP + feedback)
11. Rapports serveur (PDF/Excel)
12. Frontend React
13. Dockerisation complète (1 clic)
14. Migrations Alembic
────────── à ce stade : PFE complète ──────────
```

> 💡 **Conseil final** : reconstruis une partie à la fois, et **ne passe à la suivante que
> quand la vérification passe**. C'est exactement comme ça qu'on a construit ce projet —
> un « squelette qui marche » d'abord, puis on muscle chaque étage.
>
> Pour comprendre le rôle de chaque fichier existant, lis le compagnon
> [GUIDE_COMPLET.md](GUIDE_COMPLET.md). Pour les questions du jury, sa section 9.
