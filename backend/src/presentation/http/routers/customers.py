"""고객 관련 라우터"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.persistence.repositories.customer_repository import CustomerRepository
from src.presentation.schemas.customers import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    """고객 생성"""
    # 기존 고객이 있는지 확인
    existing_customer = CustomerRepository.get_customer_by_email(db, customer_data.email)
    if existing_customer:
        return existing_customer

    # 새로운 고객 생성
    customer = CustomerRepository.create_customer(
        db,
        email=customer_data.email,
        name=customer_data.name,
        phone=customer_data.phone,
        address=customer_data.address,
        region=customer_data.region,
    )
    return customer
