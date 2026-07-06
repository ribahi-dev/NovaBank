"""Classe de base de tous les modèles SQLAlchemy.

Pourquoi ce fichier existe :
    Chaque modèle (Client, Account, ...) doit hériter d'une classe commune
    pour que SQLAlchemy puisse les recenser. En héritant de `Base`, un modèle
    enregistre automatiquement sa table dans `Base.metadata` — le "catalogue"
    central que `create_all()` et Alembic utilisent pour créer ou migrer
    le schéma dans PostgreSQL.

Fonctionnement interne :
    `DeclarativeBase` (style SQLAlchemy 2.0) active le mode déclaratif :
    on décrit les colonnes comme des attributs de classe typés
    (`Mapped[...]` / `mapped_column(...)`), et SQLAlchemy en déduit le
    CREATE TABLE correspondant.

Ce fichier est volontairement minimal : il ne doit contenir AUCUNE logique.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
