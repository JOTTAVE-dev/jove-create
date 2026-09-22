from enum import StrEnum


class FinancialCategoryType(StrEnum):
    REVENUE = "revenue"
    PRODUCTION_COST = "production_cost"
    OPERATING_EXPENSE = "operating_expense"
    EQUIPMENT_INVESTMENT = "equipment_investment"
    INVENTORY_PURCHASE = "inventory_purchase"


class SaleStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    CANCELED = "canceled"


class SaleChannel(StrEnum):
    INSTAGRAM = "instagram"
    WHATSAPP = "whatsapp"
    SHOPEE = "shopee"
    IN_PERSON = "in_person"
    OTHER = "other"


class PaymentMethod(StrEnum):
    PIX = "pix"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    OTHER = "other"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    CANCELED = "canceled"


class PurchaseStatus(StrEnum):
    DRAFT = "draft"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELED = "canceled"


class FilamentMaterial(StrEnum):
    PLA = "PLA"
    PLA_SILK = "PLA Silk"
    PETG = "PETG"
    ABS = "ABS"
    TPU = "TPU"
    OTHER = "Outros"


class ExpenseStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"


class EquipmentStatus(StrEnum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class EquipmentKind(StrEnum):
    DURABLE = "durable"
    CONSUMABLE = "consumable"
