"""상품 관련 데이터 접근 계층"""

from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import Product


class ProductRepository:
    """Product Repository"""

    @staticmethod
    def get_product_by_id(db: Session, product_id: UUID) -> Product:
        """ID로 상품 조회"""
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_active_products(db: Session):
        """활성 상품 조회"""
        return db.query(Product).filter(Product.is_active).all()

    @staticmethod
    def create_product(
        db: Session,
        name: str,
        description: str = None,
        price: float = None,
        sku: str = None,
        image_url: str = None,
    ) -> Product:
        """상품 생성"""
        product = Product(
            name=name,
            description=description,
            price=price,
            sku=sku,
            image_url=image_url,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
