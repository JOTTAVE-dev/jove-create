"""SQLAlchemy model registry."""

from app.models.auth import AuthSession
from app.models.client import Client
from app.models.enums import (
    EquipmentStatus,
    EquipmentKind,
    ExpenseStatus,
    FinancialCategoryType,
    FilamentMaterial,
    PaymentMethod,
    PaymentStatus,
    PurchaseStatus,
    SaleChannel,
    SaleStatus,
)
from app.models.finance import Expense, FinancialCategory
from app.models.inventory import Equipment, EquipmentMaintenance, Filament, FilamentPurchase
from app.models.product import Product
from app.models.purchase import Purchase, PurchaseItem
from app.models.sale import Sale, SaleItem, SalePayment
from app.models.user import User

__all__ = [
    "Client",
    "AuthSession",
    "Equipment",
    "EquipmentKind",
    "EquipmentMaintenance",
    "EquipmentStatus",
    "Expense",
    "ExpenseStatus",
    "Filament",
    "FilamentMaterial",
    "FilamentPurchase",
    "FinancialCategory",
    "FinancialCategoryType",
    "PaymentMethod",
    "PaymentStatus",
    "Product",
    "Purchase",
    "PurchaseItem",
    "PurchaseStatus",
    "Sale",
    "SaleChannel",
    "SaleItem",
    "SalePayment",
    "SaleStatus",
    "User",
]
