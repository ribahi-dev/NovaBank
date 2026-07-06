"""Service transactions — LE cœur métier : dépôt, retrait, virement.

Points critiques implémentés ici (à connaître pour la soutenance) :

1. VERROU PESSIMISTE (`with_for_update`) : le SELECT ... FOR UPDATE de
   PostgreSQL verrouille la ligne du compte jusqu'au commit. Deux virements
   concurrents sur le même compte s'exécutent donc EN SÉRIE : impossible de
   lire un solde périmé et d'écraser la mise à jour de l'autre (lost update).

2. ORDRE DE VERROUILLAGE DÉTERMINISTE pour le virement : les deux comptes
   sont verrouillés par id croissant. Si deux virements croisés A->B et B->A
   verrouillaient chacun "source d'abord", chacun attendrait l'autre :
   deadlock. L'ordre global unique l'empêche par construction.

3. ATOMICITÉ : transaction + mise à jour des soldes + score + alerte + audit
   partent dans UN SEUL commit — tout ou rien (le A de ACID).

4. Le scoring est calculé AVANT insertion, l'alerte créée si score >= seuil.
"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Account, Alert, Transaction, User
from app.schemas.transaction import TransactionCreate
from app.services import audit_service, scoring_service


class BusinessRuleError(Exception):
    """Violation d'une règle métier — traduite en HTTP 400/409 par le router."""


def _get_locked_account(db: Session, account_id: int) -> Account:
    account = db.get(Account, account_id, with_for_update=True)
    if account is None:
        raise BusinessRuleError(f"Compte {account_id} introuvable")
    if account.status != "active":
        raise BusinessRuleError(f"Compte {account.account_number} non actif ({account.status})")
    return account


def create_transaction(
    db: Session,
    data: TransactionCreate,
    current_user: User,
    ip_address: str | None = None,
) -> Transaction:
    amount = Decimal(data.amount)

    if data.transaction_type == "transfer":
        # Verrouillage par id croissant (voir en-tête, point 2).
        first_id, second_id = sorted([data.account_id, data.destination_account_id])
        locked = {aid: _get_locked_account(db, aid) for aid in (first_id, second_id)}
        source, destination = locked[data.account_id], locked[data.destination_account_id]
        if source.balance < amount:
            raise BusinessRuleError("Solde insuffisant pour ce virement")
        source.balance -= amount
        destination.balance += amount
    else:
        source = _get_locked_account(db, data.account_id)
        if data.transaction_type == "withdrawal":
            if source.balance < amount:
                raise BusinessRuleError("Solde insuffisant pour ce retrait")
            source.balance -= amount
        else:  # deposit
            source.balance += amount

    # Scoring AVANT insertion : l'historique analysé n'inclut pas l'opération.
    result = scoring_service.score_transaction(db, source, amount, data.city)

    transaction = Transaction(
        transaction_type=data.transaction_type,
        amount=amount,
        city=data.city,
        description=data.description,
        account_id=data.account_id,
        destination_account_id=data.destination_account_id,
        created_by_id=current_user.id,
    )
    db.add(transaction)
    db.flush()  # obtient transaction.id sans committer (nécessaire aux FK suivantes)

    scoring_service.persist_score(db, transaction, result)

    if result.score >= settings.risk_alert_threshold:
        db.add(
            Alert(
                alert_type="transaction_risk",
                level="critical" if result.score >= 85 else "high",
                message=(
                    f"Score de risque {result.score}/100 sur {data.transaction_type} "
                    f"de {amount} MAD (compte {source.account_number}). {result.explanation}"
                ),
                transaction_id=transaction.id,
            )
        )

    audit_service.log_action(
        db,
        "transaction_created",
        user_id=current_user.id,
        entity_type="transaction",
        entity_id=transaction.id,
        ip_address=ip_address,
        details=f"{data.transaction_type} {amount} MAD, score {result.score}",
    )

    db.commit()
    db.refresh(transaction)
    return transaction
