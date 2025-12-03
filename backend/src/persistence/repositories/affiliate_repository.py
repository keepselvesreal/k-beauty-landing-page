"""어필리에이트 관련 데이터 접근 계층"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import Affiliate, AffiliateErrorLog, AffiliateSale


class AffiliateRepository:
    """Affiliate Repository"""

    @staticmethod
    def get_affiliate_by_code(db: Session, code: str) -> Affiliate | None:
        """Affiliate 코드로 조회"""
        return db.query(Affiliate).filter(Affiliate.code == code).first()

    @staticmethod
    def create_affiliate_error_log(
        db: Session,
        order_id: UUID,
        affiliate_code: str,
        error_type: str,
        error_message: str,
    ) -> AffiliateErrorLog:
        """Affiliate Error Log 생성"""
        error_log = AffiliateErrorLog(
            order_id=order_id,
            affiliate_code=affiliate_code,
            error_type=error_type,
            error_message=error_message,
        )
        db.add(error_log)
        db.commit()
        db.refresh(error_log)
        return error_log

    @staticmethod
    def create_affiliate_sale(
        db: Session,
        affiliate_id: UUID,
        order_id: UUID,
        marketing_commission: Decimal,
    ) -> AffiliateSale:
        """Affiliate Sale 생성 (마케팅 커미션 기록)"""
        affiliate_sale = AffiliateSale(
            affiliate_id=affiliate_id,
            order_id=order_id,
            marketing_commission=marketing_commission,
        )
        db.add(affiliate_sale)
        db.commit()
        db.refresh(affiliate_sale)
        return affiliate_sale
