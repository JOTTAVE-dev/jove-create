"""products module fields

Revision ID: 20260922_003
Revises: 20260922_002
Create Date: 2026-09-22 20:05:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_003"
down_revision: Union[str, None] = "20260922_002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.alter_column("sale_price", existing_type=sa.Numeric(12, 2), nullable=True)
        batch_op.alter_column("description", existing_type=sa.String(length=500), type_=sa.String(length=1000))
        batch_op.add_column(sa.Column("estimated_production_cost", sa.Numeric(12, 2), nullable=True))
        batch_op.add_column(sa.Column("estimated_print_time_minutes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("estimated_weight_grams", sa.Numeric(12, 3), nullable=True))
        batch_op.add_column(sa.Column("image_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("is_customizable", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.create_index("ix_products_active_category", ["is_active", "category"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_index("ix_products_active_category")
        batch_op.drop_column("is_customizable")
        batch_op.drop_column("image_url")
        batch_op.drop_column("estimated_weight_grams")
        batch_op.drop_column("estimated_print_time_minutes")
        batch_op.drop_column("estimated_production_cost")
        batch_op.alter_column("description", existing_type=sa.String(length=1000), type_=sa.String(length=500))
        batch_op.alter_column("sale_price", existing_type=sa.Numeric(12, 2), nullable=False)
