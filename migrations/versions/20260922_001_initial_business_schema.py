"""initial business schema

Revision ID: 20260922_001
Revises:
Create Date: 2026-09-22 18:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260922_001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"], unique=False)

    op.create_table(
        "clients",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("document", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document"),
    )
    op.create_index("ix_clients_id", "clients", ["id"], unique=False)
    op.create_index("ix_clients_email", "clients", ["email"], unique=False)
    op.create_index("ix_clients_name_document", "clients", ["name", "document"], unique=False)

    op.create_table(
        "products",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("sale_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_category", "products", ["category"], unique=False)
    op.create_index("ix_products_name_category", "products", ["name", "category"], unique=False)

    op.create_table(
        "filaments",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("material", sa.String(length=60), nullable=False),
        sa.Column("color", sa.String(length=80), nullable=False),
        sa.Column("diameter_mm", sa.Numeric(5, 2), nullable=True),
        sa.Column("spool_weight_grams", sa.Numeric(12, 3), nullable=True),
        sa.Column("stock_grams", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_filaments_id", "filaments", ["id"], unique=False)
    op.create_index("ix_filaments_material", "filaments", ["material"], unique=False)
    op.create_index("ix_filaments_color", "filaments", ["color"], unique=False)
    op.create_index("ix_filaments_material_color", "filaments", ["material", "color"], unique=False)

    op.create_table(
        "equipments",
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("equipment_type", sa.String(length=100), nullable=False),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
    )
    op.create_index("ix_equipments_id", "equipments", ["id"], unique=False)
    op.create_index("ix_equipments_equipment_type", "equipments", ["equipment_type"], unique=False)
    op.create_index("ix_equipments_name_status", "equipments", ["name", "status"], unique=False)

    op.create_table(
        "financial_categories",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category_type", sa.String(length=40), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_categories_id", "financial_categories", ["id"], unique=False)
    op.create_index("ix_financial_categories_category_type", "financial_categories", ["category_type"], unique=False)
    op.create_index(
        "ix_financial_categories_name_type",
        "financial_categories",
        ["name", "category_type"],
        unique=False,
    )

    op.create_table(
        "sales",
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sale_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sales_id", "sales", ["id"], unique=False)
    op.create_index("ix_sales_status", "sales", ["status"], unique=False)
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"], unique=False)
    op.create_index("ix_sales_client_status", "sales", ["client_id", "status"], unique=False)
    op.create_index("ix_sales_sale_date_status", "sales", ["sale_date", "status"], unique=False)

    op.create_table(
        "purchases",
        sa.Column("supplier_name", sa.String(length=160), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["financial_categories.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchases_id", "purchases", ["id"], unique=False)
    op.create_index("ix_purchases_supplier_name", "purchases", ["supplier_name"], unique=False)
    op.create_index("ix_purchases_status", "purchases", ["status"], unique=False)
    op.create_index("ix_purchases_purchase_date", "purchases", ["purchase_date"], unique=False)
    op.create_index("ix_purchases_category_status", "purchases", ["category_id", "status"], unique=False)
    op.create_index("ix_purchases_supplier_date", "purchases", ["supplier_name", "purchase_date"], unique=False)

    op.create_table(
        "expenses",
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("paid_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["financial_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_expenses_id", "expenses", ["id"], unique=False)
    op.create_index("ix_expenses_due_date", "expenses", ["due_date"], unique=False)
    op.create_index("ix_expenses_status", "expenses", ["status"], unique=False)
    op.create_index("ix_expenses_category_due_date", "expenses", ["category_id", "due_date"], unique=False)
    op.create_index("ix_expenses_status_due_date", "expenses", ["status", "due_date"], unique=False)

    op.create_table(
        "sale_items",
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sale_items_id", "sale_items", ["id"], unique=False)
    op.create_index("ix_sale_items_sale_product", "sale_items", ["sale_id", "product_id"], unique=False)

    op.create_table(
        "purchase_items",
        sa.Column("purchase_id", sa.Integer(), nullable=False),
        sa.Column("filament_id", sa.Integer(), nullable=True),
        sa.Column("equipment_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 3), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"]),
        sa.ForeignKeyConstraint(["filament_id"], ["filaments.id"]),
        sa.ForeignKeyConstraint(["purchase_id"], ["purchases.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_items_id", "purchase_items", ["id"], unique=False)
    op.create_index("ix_purchase_items_purchase", "purchase_items", ["purchase_id"], unique=False)
    op.create_index("ix_purchase_items_filament", "purchase_items", ["filament_id"], unique=False)
    op.create_index("ix_purchase_items_equipment", "purchase_items", ["equipment_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_purchase_items_equipment", table_name="purchase_items")
    op.drop_index("ix_purchase_items_filament", table_name="purchase_items")
    op.drop_index("ix_purchase_items_purchase", table_name="purchase_items")
    op.drop_index("ix_purchase_items_id", table_name="purchase_items")
    op.drop_table("purchase_items")

    op.drop_index("ix_sale_items_sale_product", table_name="sale_items")
    op.drop_index("ix_sale_items_id", table_name="sale_items")
    op.drop_table("sale_items")

    op.drop_index("ix_expenses_status_due_date", table_name="expenses")
    op.drop_index("ix_expenses_category_due_date", table_name="expenses")
    op.drop_index("ix_expenses_status", table_name="expenses")
    op.drop_index("ix_expenses_due_date", table_name="expenses")
    op.drop_index("ix_expenses_id", table_name="expenses")
    op.drop_table("expenses")

    op.drop_index("ix_purchases_supplier_date", table_name="purchases")
    op.drop_index("ix_purchases_category_status", table_name="purchases")
    op.drop_index("ix_purchases_purchase_date", table_name="purchases")
    op.drop_index("ix_purchases_status", table_name="purchases")
    op.drop_index("ix_purchases_supplier_name", table_name="purchases")
    op.drop_index("ix_purchases_id", table_name="purchases")
    op.drop_table("purchases")

    op.drop_index("ix_sales_sale_date_status", table_name="sales")
    op.drop_index("ix_sales_client_status", table_name="sales")
    op.drop_index("ix_sales_sale_date", table_name="sales")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_index("ix_sales_id", table_name="sales")
    op.drop_table("sales")

    op.drop_index("ix_financial_categories_name_type", table_name="financial_categories")
    op.drop_index("ix_financial_categories_category_type", table_name="financial_categories")
    op.drop_index("ix_financial_categories_id", table_name="financial_categories")
    op.drop_table("financial_categories")

    op.drop_index("ix_equipments_name_status", table_name="equipments")
    op.drop_index("ix_equipments_equipment_type", table_name="equipments")
    op.drop_index("ix_equipments_id", table_name="equipments")
    op.drop_table("equipments")

    op.drop_index("ix_filaments_material_color", table_name="filaments")
    op.drop_index("ix_filaments_color", table_name="filaments")
    op.drop_index("ix_filaments_material", table_name="filaments")
    op.drop_index("ix_filaments_id", table_name="filaments")
    op.drop_table("filaments")

    op.drop_index("ix_products_name_category", table_name="products")
    op.drop_index("ix_products_category", table_name="products")
    op.drop_index("ix_products_id", table_name="products")
    op.drop_table("products")

    op.drop_index("ix_clients_name_document", table_name="clients")
    op.drop_index("ix_clients_email", table_name="clients")
    op.drop_index("ix_clients_id", table_name="clients")
    op.drop_table("clients")

    op.drop_index("ix_users_email_active", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
