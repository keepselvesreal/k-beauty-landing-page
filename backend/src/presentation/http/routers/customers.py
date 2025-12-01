"""고객 관련 라우터"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.persistence.repositories.customer_repository import CustomerRepository
from src.presentation.schemas.customers import CustomerCreate, CustomerResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
):
    """고객 생성"""
    logger.info(f"고객 생성 요청: {customer_data.model_dump()}")

    # 기존 고객이 있는지 확인
    existing_customer = CustomerRepository.get_customer_by_email(db, customer_data.email)
    if existing_customer:
        logger.info(f"기존 고객 반환: {existing_customer.id}")
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
    logger.info(f"새로운 고객 생성: {customer.id}")
    return customer
