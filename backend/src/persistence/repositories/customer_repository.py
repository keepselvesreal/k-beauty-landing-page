"""고객 관련 데이터 접근 계층"""

from sqlalchemy.orm import Session

from src.persistence.models import Customer


class CustomerRepository:
    """Customer Repository"""

    @staticmethod
    def get_customer_by_email(db: Session, email: str) -> Customer:
        """이메일로 고객 조회"""
        return db.query(Customer).filter(Customer.email == email).first()

    @staticmethod
    def get_customer_by_id(db: Session, customer_id: str) -> Customer:
        """ID로 고객 조회"""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def create_customer(
        db: Session,
        email: str,
        name: str,
        phone: str,
        address: str,
        region: str = None,
    ) -> Customer:
        """고객 생성"""
        customer = Customer(
            email=email,
            name=name,
            phone=phone,
            address=address,
            region=region,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def update_customer(
        db: Session,
        customer_id: str,
        **kwargs
    ) -> Customer:
        """고객 정보 업데이트"""
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            for key, value in kwargs.items():
                if hasattr(customer, key) and value is not None:
                    setattr(customer, key, value)
            db.commit()
            db.refresh(customer)
        return customer
