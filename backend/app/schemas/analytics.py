"""Schemas du dashboard directeur (Modules 5 et 6 du cahier des charges)."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class KpiResponse(BaseModel):
    total_clients: int
    total_accounts: int
    total_transactions: int
    open_alerts: int
    total_deposits: Decimal
    total_withdrawals: Decimal
    average_risk_score: float | None  # None tant qu'aucune transaction scorée


class TrendPoint(BaseModel):
    day: date
    transaction_count: int
    total_amount: Decimal


class TypeDistribution(BaseModel):
    transaction_type: str
    count: int
    total_amount: Decimal
