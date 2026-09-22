from datetime import date
from decimal import Decimal

from sqlalchemy import Float, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import (
    Client,
    Equipment,
    Expense,
    ExpenseStatus,
    Filament,
    FinancialCategory,
    FinancialCategoryType,
    Product,
    Purchase,
    PurchaseItem,
    PurchaseStatus,
    Sale,
    SaleItem,
    SaleStatus,
    User,
)


def make_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    return testing_session()


def test_sale_can_contain_multiple_products() -> None:
    session = make_session()
    user = User(name="Admin", email="admin@jove.local", password_hash="hashed")
    client = Client(name="Cliente Teste", email="cliente@example.com")
    keychain = Product(name="Chaveiro 3D", sale_price=Decimal("25.00"))
    support = Product(name="Suporte 3D", sale_price=Decimal("80.00"))
    sale = Sale(
        client=client,
        user=user,
        status=SaleStatus.OPEN,
        total_amount=Decimal("130.00"),
        items=[
            SaleItem(
                product=keychain,
                product_name="Chaveiro 3D",
                quantity=Decimal("2"),
                unit_price=Decimal("25.00"),
                total_amount=Decimal("50.00"),
            ),
            SaleItem(
                product=support,
                product_name="Suporte 3D",
                quantity=Decimal("1"),
                unit_price=Decimal("80.00"),
                total_amount=Decimal("80.00"),
            ),
        ],
    )

    session.add(sale)
    session.commit()

    saved_sale = session.get(Sale, sale.id)

    assert saved_sale is not None
    assert len(saved_sale.items) == 2
    assert saved_sale.items[0].product.name == "Chaveiro 3D"
    assert saved_sale.client.name == "Cliente Teste"


def test_purchase_can_contain_filaments_and_equipment() -> None:
    session = make_session()
    category = FinancialCategory(
        name="Compras de estoque",
        category_type=FinancialCategoryType.INVENTORY_PURCHASE,
    )
    filament = Filament(
        name="PLA Marrom",
        material="PLA",
        color="Marrom",
        stock_grams=Decimal("1000.000"),
        unit_cost=Decimal("119.90"),
    )
    equipment = Equipment(
        name="Impressora reserva",
        equipment_type="Impressora 3D",
        purchase_cost=Decimal("2300.00"),
    )
    purchase = Purchase(
        supplier_name="Fornecedor Maker",
        category=category,
        status=PurchaseStatus.RECEIVED,
        total_amount=Decimal("2419.90"),
        items=[
            PurchaseItem(
                filament=filament,
                description="Rolo PLA marrom",
                quantity=Decimal("1"),
                unit_cost=Decimal("119.90"),
                total_cost=Decimal("119.90"),
            ),
            PurchaseItem(
                equipment=equipment,
                description="Impressora 3D",
                quantity=Decimal("1"),
                unit_cost=Decimal("2300.00"),
                total_cost=Decimal("2300.00"),
            ),
        ],
    )

    session.add(purchase)
    session.commit()

    saved_purchase = session.get(Purchase, purchase.id)

    assert saved_purchase is not None
    assert len(saved_purchase.items) == 2
    assert saved_purchase.items[0].filament.material == "PLA"
    assert saved_purchase.items[1].equipment.equipment_type == "Impressora 3D"


def test_financial_categories_differentiate_business_flows() -> None:
    session = make_session()
    categories = [
        FinancialCategory(name="Receitas", category_type=FinancialCategoryType.REVENUE),
        FinancialCategory(name="Custos de produção", category_type=FinancialCategoryType.PRODUCTION_COST),
        FinancialCategory(name="Despesas operacionais", category_type=FinancialCategoryType.OPERATING_EXPENSE),
        FinancialCategory(name="Investimentos", category_type=FinancialCategoryType.EQUIPMENT_INVESTMENT),
        FinancialCategory(name="Compras de estoque", category_type=FinancialCategoryType.INVENTORY_PURCHASE),
    ]

    session.add_all(categories)
    session.commit()

    saved_types = {category.category_type for category in session.query(FinancialCategory).all()}

    assert saved_types == set(FinancialCategoryType)


def test_expense_belongs_to_financial_category() -> None:
    session = make_session()
    category = FinancialCategory(
        name="Operacional",
        category_type=FinancialCategoryType.OPERATING_EXPENSE,
    )
    expense = Expense(
        category=category,
        description="Energia elétrica",
        amount=Decimal("420.00"),
        expense_date=date(2026, 9, 22),
        status=ExpenseStatus.PENDING,
    )

    session.add(expense)
    session.commit()

    saved_expense = session.get(Expense, expense.id)

    assert saved_expense is not None
    assert saved_expense.category.category_type == FinancialCategoryType.OPERATING_EXPENSE


def test_financial_columns_do_not_use_float() -> None:
    float_columns = [
        f"{table.name}.{column.name}"
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, Float)
    ]

    assert float_columns == []
