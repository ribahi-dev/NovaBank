# Plan directeur — NovaBank

> Ce document décrit la **version finale** du projet et le **chemin de codage** pour y arriver.
> Règle d'or : on ne code une étape que lorsque la précédente est **terminée, testée et comprise**.

---

## 1. Vision du produit final (ce que le jury verra)

### La démo de soutenance, minute par minute

1. **`docker compose up`** → toute la plateforme démarre (PostgreSQL + API + Frontend). Une seule commande.
2. **Connexion Conseiller** → espace de travail : recherche d'un client par CIN, fiche client
   (comptes, historique, score de risque moyen), saisie d'un dépôt puis d'un **virement**.
3. **Le virement suspect** : le conseiller saisit un virement de 45 000 DH à 02h du matin
   depuis une ville inhabituelle → l'API répond avec la transaction **ET** son score de risque
   (ex. 88/100) calculé en temps réel par le modèle ML.
4. **Connexion Directeur** → le dashboard affiche les KPI (clients, volumes, évolution
   quotidienne/mensuelle, répartition des opérations en graphiques Plotly) et un badge
   "1 nouvelle alerte".
5. **Centre d'alertes** : le directeur ouvre l'alerte, lit l'**explication lisible**
   ("Montant 3,2× supérieur aux habitudes du client ; heure inhabituelle ; ville différente"),
   la qualifie et la clôture → l'action est tracée dans le journal d'audit.
6. **Rapport** : le directeur exporte le rapport d'activité mensuel en **PDF** et **Excel**.
7. **Connexion Admin** → gestion des utilisateurs, consultation du journal d'audit
   (y compris les 5 tentatives de connexion échouées qui ont verrouillé un compte → alerte sécurité).
8. **Bonus technique pour le jury** : Swagger (`/docs`), badge CI vert sur GitHub,
   suite de tests, notebook d'évaluation du modèle (précision/rappel/AUC-PR).

### Les 3 messages que la démo doit faire passer

| Message | Preuve dans la démo |
|---|---|
| "C'est une vraie application d'entreprise" | Docker one-command, architecture en couches, tests, CI, audit |
| "L'IA n'est pas une boîte noire" | Score 0–100 + explication par variable, notebook d'évaluation honnête |
| "La sécurité est prise au sérieux" | JWT, RBAC démontré (un conseiller ne voit PAS le dashboard), verrouillage, journal |

---

## 2. Architecture finale

```
┌──────────────────────┐        ┌───────────────────────────────┐       ┌──────────────┐
│   React (SPA)        │  HTTP  │   FastAPI                     │  SQL  │  PostgreSQL  │
│                      │ ─────► │                               │ ────► │              │
│  - Login             │  JSON  │  routers/    (HTTP, validation)│       │  - tables    │
│  - Espace conseiller │  +JWT  │  services/   (logique métier) │       │  - index     │
│  - Dashboard Plotly  │        │  repositories/ (accès données)│       │  - contraintes│
│  - Centre d'alertes  │        │  schemas/    (Pydantic)       │       └──────────────┘
│  - Admin             │        │  models/     (SQLAlchemy)     │
└──────────────────────┘        │  ml/         (modèle chargé   │
                                │              au démarrage)    │
                                └───────────────────────────────┘
        Le tout conteneurisé : docker compose = postgres + api + frontend
```

**Règle de dépendance (architecture en couches)** : `routers → services → repositories → models`.
Un router ne touche JAMAIS la base directement ; un service ne connaît JAMAIS HTTP.
C'est ce qui rend le code testable et évolutif (exigence "Maintenabilité/Évolutivité" du cahier des charges).

### Structure de dossiers cible

```
NovaBank/
├── backend/
│   ├── app/
│   │   ├── core/            config.py, security.py (hash, JWT), permissions.py (RBAC)
│   │   ├── db/              base.py, session.py
│   │   ├── models/          user, client, account, transaction, risk_score, alert, audit_log, report
│   │   ├── schemas/         un fichier par entité (Create / Update / Response)
│   │   ├── repositories/    accès données pur (CRUD)
│   │   ├── services/        logique métier (virement, scoring, alertes, verrouillage login)
│   │   ├── routers/         auth, users, clients, accounts, transactions, alerts, analytics, reports
│   │   ├── ml/              features.py, model.py (chargement), explain.py
│   │   └── main.py
│   ├── alembic/             migrations versionnées
│   ├── scripts/             seed.py (données de démo), train_model.py
│   ├── tests/               test_auth, test_clients, test_transactions, test_scoring...
│   ├── Dockerfile
│   └── requirements.txt
├── ml/                      notebooks/ (génération dataset, entraînement, évaluation), artefacts modèle
├── frontend/                React (créé en Phase D)
├── db/                      (schema_cible.sql conservé comme documentation d'architecture cible)
├── docs/                    ce plan, doc API, modèle de données, captures
├── docker-compose.yml       postgres + api + frontend
└── .github/workflows/ci.yml lint + tests à chaque push
```

---

## 3. Modèle de données final (aligné cahier des charges §8.3)

Entités : `User`, `Client`, `Account`, `Transaction`, `RiskScore`, `Alert`, `AuditLog`, `Report` (à ajouter).

Décisions actées :
- **Source de vérité = modèles SQLAlchemy + Alembic.** `db/init.sql` devient `docs/schema_cible.sql`
  (architecture cible : partitions, RLS, triggers — argument d'évolutivité en soutenance).
- Rôles = enum (`admin`, `director`, `advisor`) — suffisant pour 3 rôles fixes ; les tables
  role/permission sont l'évolution documentée.
- Horodatage par la base (`server_default=func.now()`), jamais par Python.
- Soldes : mise à jour transactionnelle avec verrou (`SELECT ... FOR UPDATE`) — point technique
  fort à expliquer au jury (concurrence, ACID).
- Suppression logique partout (`is_active`) — exigence du cahier des charges (Module 2).

---

## 4. Contrat d'API (résumé)

| Module | Endpoints principaux | Accès |
|---|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | public |
| Users | `GET/POST/PATCH /users` | admin |
| Clients | `GET/POST/PATCH /clients`, `GET /clients/{id}`, `GET /clients?search=` | conseiller, directeur |
| Comptes | `GET/POST/PATCH /accounts`, `GET /accounts/{id}` | conseiller, directeur |
| Transactions | `POST /transactions` (dépôt/retrait/virement), `GET /transactions?client=&account=&from=&to=` | conseiller |
| Scoring | (interne, appelé par le service transaction) + `GET /transactions/{id}/risk` | directeur |
| Alertes | `GET /alerts?status=`, `GET /alerts/{id}`, `PATCH /alerts/{id}` (qualifier/clôturer) | directeur |
| Analytics | `GET /analytics/kpi`, `GET /analytics/trends?period=` | directeur |
| Rapports | `POST /reports` → PDF/Excel téléchargeable | directeur, admin |
| Audit | `GET /audit-logs?user=&action=` | admin |

Chaque réponse d'erreur suit un format unique `{detail, code}` — cohérence = professionnalisme.

---

## 5. Plan de codage — l'ordre exact, étape par étape

> Stratégie senior : **squelette qui marche de bout en bout d'abord** (walking skeleton),
> puis on muscle. Jamais 3 semaines sur une couche sans rien d'exécutable.

### PHASE A — Fondations saines (≈ 2 jours)

| # | Étape | Definition of Done | Ce que tu maîtrises |
|---|---|---|---|
| A1 | Assainir : init.sql → docs/, `func.now()`, PyJWT, psycopg3, noms `novabank`, `.env` Docker | `docker compose up` + tables créées + `/health` OK | source de vérité, config 12-factor |
| A2 | Discipline git : branches `main`/`develop`/`feature/*`, conventional commits | 1er commit propre poussé | workflow d'équipe (vous êtes 3 !) |
| A3 | CI GitHub Actions minimale (lint ruff + pytest vide) | badge vert sur le README | CI/CD — rare chez les étudiants |

### PHASE B — Le socle backend (≈ 1,5 semaine) — cœur de l'apprentissage

| # | Étape | Definition of Done | Ce que tu maîtrises |
|---|---|---|---|
| B1 | Schemas Pydantic (Client d'abord) | validation testée dans Swagger | pourquoi on ne renvoie jamais un modèle SQLAlchemy |
| B2 | Repository Client + router `GET/POST/PATCH /clients` | CRUD complet visible dans Swagger | Depends(get_db), injection de dépendances |
| B3 | Idem Account puis Transaction (lecture seule) | fiche client avec ses comptes | relations, jointures, N+1 |
| B4 | **Auth** : hash bcrypt, login JWT, refresh token, `get_current_user` | login fonctionnel, routes protégées | sécurité API (OWASP) |
| B5 | **RBAC** : dépendance `require_role(...)`, verrouillage après 5 échecs, audit log des actions sensibles | un conseiller reçoit 403 sur `/users` | autorisation ≠ authentification |
| B6 | **Service virement** : validation métier, verrou `FOR UPDATE`, transaction atomique | test : 2 virements concurrents ne corrompent jamais un solde | ACID en pratique — le point fort technique |
| B7 | Alembic initialisé, première migration | `alembic upgrade head` remplace create_tables.py | migrations en entreprise |
| B8 | Tests pytest (base SQLite/testcontainer + TestClient) sur auth, clients, virement | ~25 tests verts en CI | tests = préreq de tout le reste |

### PHASE C — Données & IA (≈ 1,5 semaine)

| # | Étape | Definition of Done | Ce que tu maîtrises |
|---|---|---|---|
| C1 | `scripts/seed.py` : 50 clients marocains simulés, 30 jours de transactions réalistes, ~5 % anormales | base de démo en 1 commande | génération de données statistiquement réaliste (§9.1) |
| C2 | Feature engineering : écart au montant habituel, heure inhabituelle, fréquence 24h, changement de ville, ancienneté | dataframe de features documenté | la vraie valeur d'un modèle = ses features |
| C3 | Baseline **moteur de règles** (`mvp-rules-v1`) branché sur la création de transaction | score + explication en réponse API | toujours une baseline avant le ML |
| C4 | Entraînement **Isolation Forest + Random Forest** (notebook), évaluation précision/rappel/AUC-PR, comparaison avec la baseline | notebook d'évaluation honnête (pas d'accuracy seule — cf. cahier des charges §2.3) | méthodologie ML rigoureuse |
| C5 | Intégration : modèle chargé au démarrage, `model_version` stocké, explication par contribution des features | alerte auto créée si score > seuil | MLOps minimal (versionnage du modèle) |
| C6 | Analytics : endpoints KPI/tendances (Pandas sur requêtes SQL) | JSON prêt pour les graphiques | agrégations efficaces |

### PHASE D — Frontend React (≈ 1,5 semaine, parallélisable dans le trinôme dès B4)

| # | Étape | Definition of Done |
|---|---|---|
| D1 | Setup Vite + React Router + Axios (intercepteur JWT + refresh auto) | login → token stocké → route protégée |
| D2 | Layout par rôle (le menu dépend du rôle) | conseiller et directeur voient des menus différents |
| D3 | Espace conseiller : clients (liste/recherche/fiche), comptes, saisie transaction | flux complet de saisie |
| D4 | Dashboard directeur : KPI + graphiques Plotly | 4 graphiques interactifs |
| D5 | Centre d'alertes : liste, détail avec explication IA, qualification/clôture | cycle de vie complet d'une alerte |
| D6 | Admin : gestion utilisateurs + journal d'audit | — |

### PHASE E — Finition professionnelle (≈ 1 semaine)

| # | Étape | Definition of Done |
|---|---|---|
| E1 | Rapports PDF (reportlab) + Excel (openpyxl) | export téléchargeable depuis le dashboard |
| E2 | Dockerfile backend + frontend, compose complet, healthchecks | `docker compose up` = plateforme entière |
| E3 | Durcissement : rate limiting login, CORS strict, en-têtes sécurité, revue OWASP API Top 10 | checklist OWASP documentée |
| E4 | README d'exception : GIF démo, diagramme, badges, "Décisions techniques", quickstart 3 lignes | un recruteur comprend le projet en 90 s |
| E5 | Répétition de la démo scénarisée + plan B (vidéo enregistrée) | démo fluide en < 10 min |

### Correspondance avec le planning du cahier des charges

S1–S2 (analyse, conception) = fait. **S3 = Phases A+B1–B5 · S4 = B6–B8 + D1–D3 · S5 = C6+D4 ·
S6 = C1–C5 · S7 = D5–D6+E1+E3 · S8 = E2+E4+E5 + rapport.**
Répartition trinôme naturelle dès la fin de B4 : 1 personne backend/IA, 1 frontend, 1 flottante
(tests, seed, doc, rapport au fil de l'eau — cf. risque n°4 du cahier des charges).

---

## 6. Deux incohérences du cahier des charges à trancher (avec l'encadrante)

1. **SHAP** : l'état de l'art le recommande, mais le périmètre MVP (§3.2) l'exclut explicitement.
   → Plan retenu : explication par contribution de features maison dans le MVP (conforme §9.1),
   SHAP en *stretch goal* de S7 si l'avance le permet — les deux discours sont prêts pour le jury.
2. **bcrypt vs Argon2** : le cahier des charges impose bcrypt → on suit le document (cohérence devant
   le jury), en mentionnant Argon2 dans les perspectives. Implémentation via `pwdlib[bcrypt]`
   (passlib est abandonné et incompatible bcrypt ≥ 4.1).

---

## 7. Checklist "projet impressionnant" (à cocher avant la soutenance)

- [ ] `git clone` + `docker compose up` + 1 commande de seed = démo complète sur n'importe quel PC
- [ ] Badge CI vert, ≥ 40 tests, historique git propre (conventional commits, 3 contributeurs visibles)
- [ ] README avec GIF de démo, architecture, décisions techniques justifiées
- [ ] Notebook d'évaluation ML avec métriques adaptées au déséquilibre (précision/rappel/AUC-PR)
- [ ] Démo RBAC en live (403 du conseiller sur le dashboard) + verrouillage de compte en live
- [ ] Explication IA lisible affichée dans l'alerte
- [ ] Export PDF/Excel fonctionnel
- [ ] Rapport rédigé au fil de l'eau, chapitre sécurité aligné OWASP API Top 10
