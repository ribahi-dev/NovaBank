"""Dashboard directeur : KPI, tendances, répartition (CdC Modules 5 et 6).

Les agrégations sont faites PAR POSTGRESQL (func.count/sum/avg) : on ne
rapatrie jamais des milliers de lignes pour les additionner en Python.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.session import get_db
from app.models import Account, Alert, Client, RiskScore, Transaction
from app.schemas.analytics import KpiResponse, TrendPoint, TypeDistribution

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
    dependencies=[Depends(require_role("director"))],
)

ZERO = Decimal("0")


@router.get("/kpi", response_model=KpiResponse)
def get_kpi(db: Annotated[Session, Depends(get_db)]):
    sums = db.execute(
        select(
            func.coalesce(
                func.sum(Transaction.amount).filter(Transaction.transaction_type == "deposit"), ZERO
            ),
            func.coalesce(
                func.sum(Transaction.amount).filter(Transaction.transaction_type == "withdrawal"), ZERO
            ),
        )
    ).one()

    return KpiResponse(
        total_clients=db.scalar(select(func.count()).select_from(Client).where(Client.is_active.is_(True))),
        total_accounts=db.scalar(select(func.count()).select_from(Account)),
        total_transactions=db.scalar(select(func.count()).select_from(Transaction)),
        open_alerts=db.scalar(select(func.count()).select_from(Alert).where(Alert.status == "open")),
        total_deposits=sums[0],
        total_withdrawals=sums[1],
        average_risk_score=db.scalar(select(func.avg(RiskScore.score))),
    )


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(db: Annotated[Session, Depends(get_db)], days: int = 30):
    since = datetime.now(timezone.utc) - timedelta(days=min(days, 365))
    day = func.date_trunc("day", Transaction.created_at).label("day")
    rows = db.execute(
        select(day, func.count().label("n"), func.sum(Transaction.amount).label("total"))
        .where(Transaction.created_at >= since)
        .group_by(day)
        .order_by(day)
    ).all()
    return [
        TrendPoint(day=row.day.date(), transaction_count=row.n, total_amount=row.total or ZERO)
        for row in rows
    ]


@router.get("/distribution", response_model=list[TypeDistribution])
def get_type_distribution(db: Annotated[Session, Depends(get_db)]):
    rows = db.execute(
        select(
            Transaction.transaction_type,
            func.count().label("n"),
            func.sum(Transaction.amount).label("total"),
        ).group_by(Transaction.transaction_type)
    ).all()
    return [
        TypeDistribution(transaction_type=row.transaction_type, count=row.n, total_amount=row.total or ZERO)
        for row in rows
    ]
