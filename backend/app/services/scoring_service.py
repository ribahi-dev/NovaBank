"""Moteur de scoring de risque — double moteur derrière une interface unique.

    extract_features (app/ml/features.py — code partagé train/inférence)
            │
            ├── modèle ML (RandomForest) si un artefact entraîné existe
            │        -> model_version = "ml-rf-v2.0"
            └── sinon moteur de RÈGLES pondérées (baseline)
                     -> model_version = "mvp-rules-v1"

Dans les deux cas la sortie respecte le contrat du CdC §9.2 : score 0-100,
niveau de confiance, EXPLICATION lisible par un directeur d'agence.
La baseline n'est pas jetée quand le ML arrive : elle sert de comparaison
chiffrée (voir scripts/train_model.py) et de secours opérationnel.
"""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.ml import model as ml_model
from app.ml.features import TransactionFeatures, explain_features, extract_features
from app.models import Account, RiskScore, Transaction

RULES_VERSION = "mvp-rules-v1"


@dataclass
class ScoringResult:
    score: int
    confidence_level: str
    explanation: str
    model_version: str
    shap_values: dict[str, float] | None = None  # contributions XAI (ML seulement)


def _rules_score(f: TransactionFeatures) -> int:
    """Baseline : somme pondérée des signaux (poids validés en Phase B)."""
    score = 0
    if f.amount_over_income >= 2:
        score += 45
    elif f.amount_over_income >= 1:
        score += 30
    elif f.amount_over_income >= 0.5:
        score += 12
    elif f.amount_over_avg >= 5:
        score += 40
    elif f.amount_over_avg >= 3:
        score += 25
    if f.is_night:
        score += 25
    if f.city_changed:
        score += 20
    if f.tx_last_24h >= 5:
        score += 15
    return min(100, score)


def score_transaction(db: Session, account: Account, amount: Decimal, city: str | None) -> ScoringResult:
    features = extract_features(db, account, amount, city)
    reasons = explain_features(features)

    shap_values = None
    if ml_model.is_available():
        score = ml_model.predict_score(features)
        version = ml_model.version() or "ml-unknown"
        # SHAP : explique la décision du modèle variable par variable (XAI).
        shap_values = ml_model.explain_shap(features)
    else:
        score = _rules_score(features)
        version = RULES_VERSION

    confidence = "élevé" if len(reasons) >= 2 else "moyen" if len(reasons) == 1 else "faible"
    explanation = (
        "Transaction sans signal de risque particulier."
        if not reasons
        else "Signaux détectés : " + " ; ".join(reasons) + "."
    )
    return ScoringResult(
        score=score, confidence_level=confidence, explanation=explanation,
        model_version=version, shap_values=shap_values,
    )


def persist_score(db: Session, transaction: Transaction, result: ScoringResult) -> RiskScore:
    risk = RiskScore(
        transaction_id=transaction.id,
        score=result.score,
        confidence_level=result.confidence_level,
        explanation=result.explanation,
        model_version=result.model_version,
        shap_values=result.shap_values,
    )
    db.add(risk)
    return risk
