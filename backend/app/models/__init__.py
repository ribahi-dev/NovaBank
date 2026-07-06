"""Regroupe tous les modèles SQLAlchemy du projet.

Ce fichier a DEUX fonctions, pas seulement esthétiques :

1. Import pratique : `from app.models import Client, Account` au lieu
   d'un import par fichier.

2. ENREGISTREMENT des modèles — le point subtil : une classe SQLAlchemy
   n'inscrit sa table dans Base.metadata QUE si son module est importé.
   Importer `app.models` importe donc tous les modèles d'un coup ; c'est
   ce que font create_tables.py (et bientôt Alembic) pour "voir" toutes
   les tables. Oublier d'ajouter un nouveau modèle ici = table jamais
   créée, et l'erreur n'apparaît qu'à la première requête qui la touche.
"""

from app.models.account import Account
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.models.risk_score import RiskScore
from app.models.transaction import Transaction
from app.models.user import User

__all__ = [
    "Account",
    "Alert",
    "AuditLog",
    "Client",
    "RiskScore",
    "Transaction",
    "User",
]

