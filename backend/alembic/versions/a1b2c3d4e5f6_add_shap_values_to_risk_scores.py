"""add shap_values to risk_scores

Ajoute la colonne JSON shap_values à risk_scores pour stocker les
contributions SHAP (explicabilité XAI) de chaque variable au score.
NULL quand le score provient du moteur de règles.

Revision ID: a1b2c3d4e5f6
Revises: 55c4f769e4c7
Create Date: 2026-07-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "55c4f769e4c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("risk_scores", sa.Column("shap_values", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("risk_scores", "shap_values")
