# 🤖 Module IA — méthodologie et évaluation (version PFE)

> Ce document décrit la démarche de Machine Learning du projet et les résultats
> d'évaluation. Il est destiné à justifier nos choix devant le jury, avec des
> chiffres **honnêtes et reproductibles**.

## 1. Le problème

Détecter, parmi les transactions d'une agence, celles qui sont **anormales**. C'est un
problème de **classification binaire fortement déséquilibré** : la fraude est rare
(moins de 2 % des opérations). Ce déséquilibre est le défi central du domaine.

## 2. Les caractéristiques (features)

Chaque transaction est transformée en **5 signaux numériques**, calculés par un code
**partagé entre l'entraînement et l'inférence** (`app/ml/features.py`) — pour éviter
tout écart entre les deux (*training/serving skew*, bug classique du ML) :

| Feature | Signification |
|---|---|
| `amount_over_income` | montant ÷ revenu mensuel du client |
| `amount_over_avg` | montant ÷ moyenne historique du compte |
| `is_night` | opération entre 00h et 06h (0/1) |
| `city_changed` | ville différente de l'opération précédente (0/1) |
| `tx_last_24h` | nombre d'opérations du compte sur 24h |

## 3. Les données

Faute d'accès à des données bancaires réelles (hors périmètre du stage), nous générons un
**jeu simulé statistiquement réaliste** (`scripts/train_model.py`, ~10 000 transactions,
1,5 % de fraudes). Point méthodologique **essentiel** : nous avons introduit un
**chevauchement volontaire entre les classes** —

- ~7 % des transactions **légitimes** sont "atypiques" (salaire, loyer, achat
  exceptionnel, déplacement) ;
- 20 % des **fraudes** suivent un profil "discret", volontairement proche du légitime.

Sans ce chevauchement, le problème serait trivialement séparable et les métriques
seraient **artificiellement parfaites** — ce qui n'aurait aucune valeur scientifique.

## 4. Les modèles comparés

| Modèle | Type | Rôle |
|---|---|---|
| **Moteur de règles** (`mvp-rules-v1`) | Heuristique | Baseline de référence à battre |
| **Isolation Forest** | Non supervisé | Alternative sans étiquettes |
| **Random Forest** (`ml-rf-v2.0`) | Supervisé | Modèle retenu |

Le Random Forest est entraîné avec `class_weight="balanced"` pour compenser le
déséquilibre **sans rééchantillonnage artificiel** (nous évitons SMOTE, qui peut dégrader
la fidélité des explications — cf. état de l'art).

## 5. Les métriques

Nous évaluons avec **précision, rappel, F1 et AUC-PR** — **jamais l'exactitude
(accuracy) seule**, trompeuse à 98,5 % de classe majoritaire. Résultats sur le jeu de
test (3 000 transactions jamais vues, seuil d'alerte = 70) :

| Modèle | Précision | Rappel | F1 | AUC-PR |
|---|---|---|---|---|
| Règles (baseline) | 0,545 | 0,400 | 0,462 | 0,454 |
| Isolation Forest | 0,313 | 0,689 | 0,431 | 0,562 |
| **Random Forest (retenu)** | **0,634** | **0,578** | **0,605** | **0,589** |

> **Lecture** : le Random Forest **surpasse la baseline de règles sur toutes les
> métriques** (F1 0,61 vs 0,46 ; AUC-PR 0,59 vs 0,45). Les valeurs absolues modérées
> reflètent la **difficulté réelle** du problème (fraude rare et partiellement
> indiscernable) — nous avons **refusé de gonfler artificiellement** les résultats.

### Importance des variables (Random Forest)

| Feature | Importance |
|---|---|
| `amount_over_income` | 0,385 |
| `amount_over_avg` | 0,295 |
| `city_changed` | 0,134 |
| `is_night` | 0,119 |
| `tx_last_24h` | 0,067 |

Le montant rapporté au profil du client est, logiquement, le signal le plus discriminant.

## 6. Intégration dans l'application

Le scoring possède **deux moteurs derrière une interface unique**
(`app/services/scoring_service.py`) :

1. **Modèle ML** (Random Forest) si un artefact entraîné est présent → `ml-rf-v2.0` ;
2. **Repli automatique** sur le moteur de règles sinon → `mvp-rules-v1`.

L'application n'est **jamais** en panne de scoring. Chaque score enregistré garde la
**trace du moteur** l'ayant produit (`model_version`) — principe de traçabilité (MLOps).
Dans l'image Docker, le modèle est **entraîné au moment de la construction** et donc
directement actif.

## 7. La boucle de feedback (human-in-the-loop) ⭐

C'est notre différenciation. Quand le directeur **clôture une alerte**, il la **qualifie**
(`confirmed_fraud` ou `false_positive`). Ces qualifications sont stockées et deviennent
des **étiquettes d'entraînement** pour le prochain modèle (`load_feedback_labels()`).

Autrement dit, **le système apprend des décisions de l'agence**. Cela répond directement
à la limite des solutions commerciales (Feedzai, SAS…), qui dépendent de gigantesques
bases de données étiquetées externes : ici, la donnée d'apprentissage naît du travail
quotidien du directeur.

## 8. Reproductibilité

Tout est reproductible (graine aléatoire fixée). Pour régénérer le modèle et les
métriques :

```bash
cd backend
python -m scripts.train_model
# -> ml_artifacts/model.joblib + ml_artifacts/metrics.json
```

## 8 bis. Explicabilité SHAP (XAI) — intégrée

Pour chaque transaction scorée par le modèle, nous calculons les **valeurs SHAP**
(`app/ml/model.py`, `shap.TreeExplainer`). SHAP répartit le score entre les variables
selon une base mathématique solide (valeurs de Shapley, théorie des jeux) : une
contribution **positive pousse vers la fraude**, **négative vers le normal**.

Ces contributions sont **stockées** avec le score (`risk_scores.shap_values`, JSON) et
**affichées** dans l'interface sous forme de barres bidirectionnelles — le directeur voit
non seulement *que* la transaction est risquée, mais *pourquoi*, variable par variable.
C'est la méthode de référence de l'état de l'art, et un argument fort de conformité
(explicabilité exigée par le RGPD / l'EU AI Act).

L'implémentation est **robuste** : si SHAP n'est pas disponible, la fonction renvoie
`None` et l'application continue avec l'explication textuelle — jamais de panne.

## 9. Limites et perspectives

- **Données simulées** : validées statistiquement, mais pas réelles (décision DSI).
- **Réentraînement** : aujourd'hui manuel (ou au build de l'image) ; une automatisation
  périodique, déclenchée par le volume de feedback, est envisagée.
- **Modèles avancés** : XGBoost / LightGBM pourraient être comparés au Random Forest.
