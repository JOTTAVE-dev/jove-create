from sqlalchemy.orm import Session

from app.models import Product
from app.repositories import products as product_repository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductNotFoundError(ValueError):
    pass


def list_products(db: Session, query: str | None = None, include_inactive: bool = False) -> list[Product]:
    return product_repository.list_products(db, query=query, include_inactive=include_inactive)


def get_product_or_raise(db: Session, product_id: int) -> Product:
    product = product_repository.get_product(db, product_id)
    if product is None:
        raise ProductNotFoundError("Produto nao encontrado.")
    return product


def create_product(db: Session, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    return product_repository.create_product(db, product)


def update_product(db: Session, product_id: int, payload: ProductUpdate) -> Product:
    product = get_product_or_raise(db, product_id)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    return product_repository.save_product(db, product)


def deactivate_product(db: Session, product_id: int) -> Product:
    product = get_product_or_raise(db, product_id)
    product.is_active = False
    return product_repository.save_product(db, product)
