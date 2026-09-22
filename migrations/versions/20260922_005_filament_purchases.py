"""filament purchases

Revision ID: 20260922_005
Revises: 20260922_004
Create Date: 2026-09-22 21:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_005"
down_revision: Union[str, None] = "20260922_004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "filament_purchases",
        sa.Column("filament_id", sa.Integer(), nullable=True),
        sa.Column("brand", sa.String(length=120), nullable=False),
        sa.Column("material", sa.String(length=32), nullable=False),
        sa.Column("color", sa.String(length=80), nullable=False),
        sa.Column("weight_grams", sa.Numeric(12, 3), nullable=False),
        sa.Column("material_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("shipping_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("cost_per_gram", sa.Numeric(12, 6), nullable=False),
        sa.Column("supplier", sa.String(length=160), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["filament_id"], ["filaments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_filament_purchases_id", "filament_purchases", ["id"], unique=False)
    op.create_index("ix_filament_purchases_material", "filament_purchases", ["material"], unique=False)
    op.create_index("ix_filament_purchases_color", "filament_purchases", ["color"], unique=False)
    op.create_index("ix_filament_purchases_supplier", "filament_purchases", ["supplier"], unique=False)
    op.create_index("ix_filament_purchases_purchase_date", "filament_purchases", ["purchase_date"], unique=False)
    op.create_index(
        "ix_filament_purchases_material_color",
        "filament_purchases",
        ["material", "color"],
        unique=False,
    )
    op.create_index(
        "ix_filament_purchases_supplier_date",
        "filament_purchases",
        ["supplier", "purchase_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_filament_purchases_supplier_date", table_name="filament_purchases")
    op.drop_index("ix_filament_purchases_material_color", table_name="filament_purchases")
    op.drop_index("ix_filament_purchases_purchase_date", table_name="filament_purchases")
    op.drop_index("ix_filament_purchases_supplier", table_name="filament_purchases")
    op.drop_index("ix_filament_purchases_color", table_name="filament_purchases")
    op.drop_index("ix_filament_purchases_material", table_name="filament_purchases")
    op.drop_index("ix_filament_purchases_id", table_name="filament_purchases")
    op.drop_table("filament_purchases")
