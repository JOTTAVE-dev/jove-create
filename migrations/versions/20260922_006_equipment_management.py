"""equipment management

Revision ID: 20260922_006
Revises: 20260922_005
Create Date: 2026-09-22 22:20:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_006"
down_revision: Union[str, None] = "20260922_005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("equipments") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=100), nullable=False, server_default="Equipamento"))
        batch_op.add_column(sa.Column("kind", sa.String(length=32), nullable=False, server_default="durable"))
        batch_op.add_column(sa.Column("manufacturer", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("model", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("supplier", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("estimated_life_months", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.String(length=500), nullable=True))
        batch_op.create_index("ix_equipments_category", ["category"], unique=False)
        batch_op.create_index("ix_equipments_kind", ["kind"], unique=False)
        batch_op.create_index("ix_equipments_supplier", ["supplier"], unique=False)
        batch_op.create_index("ix_equipments_category_kind", ["category", "kind"], unique=False)

    op.create_table(
        "equipment_maintenances",
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("maintenance_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("supplier", sa.String(length=160), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_equipment_maintenances_id", "equipment_maintenances", ["id"], unique=False)
    op.create_index("ix_equipment_maintenances_maintenance_date", "equipment_maintenances", ["maintenance_date"], unique=False)
    op.create_index(
        "ix_equipment_maintenances_equipment_date",
        "equipment_maintenances",
        ["equipment_id", "maintenance_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_equipment_maintenances_equipment_date", table_name="equipment_maintenances")
    op.drop_index("ix_equipment_maintenances_maintenance_date", table_name="equipment_maintenances")
    op.drop_index("ix_equipment_maintenances_id", table_name="equipment_maintenances")
    op.drop_table("equipment_maintenances")

    with op.batch_alter_table("equipments") as batch_op:
        batch_op.drop_index("ix_equipments_category_kind")
        batch_op.drop_index("ix_equipments_supplier")
        batch_op.drop_index("ix_equipments_kind")
        batch_op.drop_index("ix_equipments_category")
        batch_op.drop_column("notes")
        batch_op.drop_column("estimated_life_months")
        batch_op.drop_column("supplier")
        batch_op.drop_column("model")
        batch_op.drop_column("manufacturer")
        batch_op.drop_column("kind")
        batch_op.drop_column("category")
