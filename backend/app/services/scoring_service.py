"""Moteur de scoring de risque — version 1 : règles métier (mvp-rules-v1).

Stratégie du plan directeur : une BASELINE de règles interprétables branchée
dès maintenant, que le modèle ML (Phase C) remplacera derrière la même
interface. Le contrat ne change pas : score 0-100 + confiance + explication
lisible (CdC §9.1/9.2).

Facteurs évalués (chacun contribue au score et à l'explication) :
  - montant vs revenu mensuel du client (ou vs historique du compte) ;
  - heure inhabituelle (00h-06h) ;
  - changement de ville par rapport à l'opération précédente ;
  - fréquence anormale sur 24h.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, RiskScore, Transaction

MODEL_VERSION = "mvp-rules-v1"


@dataclass
class ScoringResult:
    score: int
    confidence_level: str
    explanation: str


def _amount_factor(db: Session, account: Account, amount: Decimal) -> tuple[int, str | None]:
    income = account.client.monthly_income if account.client else None
    if income and income > 0:
        ratio = float(amount / income)
        if ratio >= 2:
            return 45, f"montant {ratio:.1f}x supérieur au revenu mensuel du client"
        if ratio >= 1:
            return 30, f"montant équivalent à {ratio:.1f}x le revenu mensuel du client"
        if ratio >= 0.5:
            return 12, "montant représentant plus de la moitié du revenu mensuel"
        return 0, None

    # Pas de revenu connu : comparaison à la moyenne historique du compte.
    avg = db.scalar(
        select(func.avg(Transaction.amount)).where(Transaction.account_id == account.id)
    )
    if avg and avg > 0:
        ratio = float(amount / avg)
        if ratio >= 5:
            return 40, f"montant {ratio:.1f}x supérieur à la moyenne du compte"
        if ratio >= 3:
            return 25, f"montant {ratio:.1f}x supérieur à la moyenne du compte"
    return 0, None


def _hour_factor(moment: datetime) -> tuple[int, str | None]:
    if 0 <= moment.hour < 6:
        return 25, f"opération à {moment.strftime('%Hh%M')}, hors des horaires habituels"
    return 0, None


def _city_factor(db: Session, account: Account, city: str | None) -> tuple[int, str | None]:
    if not city:
        return 0, None
    last_city = db.scalar(
        select(Transaction.city)
        .where(Transaction.account_id == account.id, Transaction.city.is_not(None))
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    if last_city and last_city.strip().lower() != city.strip().lower():
        return 20, f"ville inhabituelle ({city}, précédente : {last_city})"
    return 0, None


def _frequency_factor(db: Session, account: Account) -> tuple[int, str | None]:
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    count = db.scalar(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.account_id == account.id, Transaction.created_at >= since)
    )
    if count and count >= 5:
        return 15, f"{count} opérations sur les dernières 24h"
    return 0, None


def score_transaction(db: Session, account: Account, amount: Decimal, city: str | None) -> ScoringResult:
    """Évalue le risque AVANT insertion de la transaction (l'historique
    interrogé ne contient donc pas l'opération en cours d'analyse)."""
    factors = [
        _amount_factor(db, account, amount),
        _hour_factor(datetime.now()),
        _city_factor(db, account, city),
        _frequency_factor(db, account),
    ]
    score = min(100, sum(points for points, _ in factors))
    reasons = [reason for _, reason in factors if reason]

    triggered = len(reasons)
    confidence = "élevé" if triggered >= 2 else "moyen" if triggered == 1 else "faible"
    explanation = (
        "Transaction sans signal de risque particulier."
        if not reasons
        else "Signaux détectés : " + " ; ".join(reasons) + "."
    )
    return ScoringResult(score=score, confidence_level=confidence, explanation=explanation)


def persist_score(db: Session, transaction: Transaction, result: ScoringResult) -> RiskScore:
    risk = RiskScore(
        transaction_id=transaction.id,
        score=result.score,
        confidence_level=result.confidence_level,
        explanation=result.explanation,
        model_version=MODEL_VERSION,
    )
    db.add(risk)
    return risk
