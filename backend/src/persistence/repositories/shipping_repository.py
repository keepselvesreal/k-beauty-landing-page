"""배송료 관련 데이터 접근 계층"""

from typing import List

from sqlalchemy.orm import Session

from src.persistence.models import ShippingRate


class ShippingRepository:
    """배송료 Repository"""

    @staticmethod
    def get_all_shipping_rates(db: Session) -> List[ShippingRate]:
        """모든 배송료 조회"""
        return db.query(ShippingRate).all()

    @staticmethod
    def get_shipping_rate_by_region(db: Session, region: str) -> ShippingRate:
        """지역별 배송료 조회"""
        return db.query(ShippingRate).filter(ShippingRate.region == region).first()

    @staticmethod
    def create_shipping_rate(db: Session, region: str, fee: float) -> ShippingRate:
        """배송료 생성"""
        shipping_rate = ShippingRate(region=region, fee=fee)
        db.add(shipping_rate)
        db.commit()
        db.refresh(shipping_rate)
        return shipping_rate

    @staticmethod
    def update_shipping_rate(db: Session, region: str, fee: float) -> ShippingRate:
        """배송료 업데이트"""
        shipping_rate = db.query(ShippingRate).filter(ShippingRate.region == region).first()
        if shipping_rate:
            shipping_rate.fee = fee
            db.commit()
            db.refresh(shipping_rate)
        return shipping_rate
