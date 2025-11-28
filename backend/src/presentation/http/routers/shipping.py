"""배송료 관련 라우터"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.persistence.repositories.shipping_repository import ShippingRepository
from src.presentation.schemas.shipping import ShippingRateResponse, ShippingRateUpdate

router = APIRouter(prefix="/api/shipping-rates", tags=["shipping"])


@router.get("", response_model=List[ShippingRateResponse])
async def get_all_shipping_rates(db: Session = Depends(get_db)):
    """모든 배송료 조회"""
    rates = ShippingRepository.get_all_shipping_rates(db)
    return rates


@router.get("/{region}", response_model=ShippingRateResponse)
async def get_shipping_rate(region: str, db: Session = Depends(get_db)):
    """지역별 배송료 조회"""
    rate = ShippingRepository.get_shipping_rate_by_region(db, region)
    if not rate:
        return {"error": f"Shipping rate for region '{region}' not found"}
    return rate


@router.put("/{region}", response_model=ShippingRateResponse)
async def update_shipping_rate(
    region: str,
    update_data: ShippingRateUpdate,
    db: Session = Depends(get_db),
):
    """배송료 업데이트"""
    rate = ShippingRepository.update_shipping_rate(db, region, update_data.fee)
    if not rate:
        return {"error": f"Shipping rate for region '{region}' not found"}
    return rate
