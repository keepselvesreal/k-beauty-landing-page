"""어필리에이트 비즈니스 로직 서비스"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import Order, Settings
from src.persistence.repositories.affiliate_repository import AffiliateRepository


class AffiliateService:
    """Affiliate Service"""

    @staticmethod
    def calculate_commission(profit: Decimal, commission_rate: Decimal) -> Decimal:
        """Commission 계산

        Args:
            profit: 주문 이윤
            commission_rate: 수수료율 (0.2 = 20%)

        Returns:
            계산된 Commission 금액
        """
        return profit * commission_rate

    @staticmethod
    def record_commission_if_applicable(db: Session, order: Order) -> None:
        """주문에 대한 Commission 기록 (Affiliate ID가 유효한 경우만)

        Args:
            db: 데이터베이스 세션
            order: 주문 객체

        Returns:
            None
        """
        # 1. Affiliate ID가 없으면 기록하지 않음
        if not order.affiliate_id:
            return

        # 2. Settings에서 Commission Rate 조회
        settings = db.query(Settings).first()
        if not settings:
            return

        # 3. Commission 계산
        commission_amount = AffiliateService.calculate_commission(
            order.profit,
            settings.affiliate_commission_rate,
        )

        # 4. Affiliate Sale 기록
        AffiliateRepository.create_affiliate_sale(
            db,
            affiliate_id=order.affiliate_id,
            order_id=order.id,
            commission_amount=commission_amount,
        )

    @staticmethod
    def validate_and_record_affiliate_on_order_creation(
        db: Session,
        order: Order,
        affiliate_code: str | None,
    ) -> UUID | None:
        """Order 생성 시 Affiliate 코드 검증 및 오류 기록

        Args:
            db: 데이터베이스 세션
            order: 주문 객체
            affiliate_code: Affiliate 코드 (선택사항)

        Returns:
            유효한 Affiliate ID 또는 None
        """
        # 1. Affiliate code가 없으면 None 반환
        if not affiliate_code:
            return None

        # 2. Affiliate 코드로 조회
        affiliate = AffiliateRepository.get_affiliate_by_code(db, affiliate_code)

        # 3. Affiliate가 없으면 오류 기록
        if not affiliate:
            AffiliateRepository.create_affiliate_error_log(
                db,
                order_id=order.id,
                affiliate_code=affiliate_code,
                error_type="INVALID_CODE",
                error_message="Affiliate code not found",
            )
            return None

        # 4. Affiliate가 비활성화되면 오류 기록
        if not affiliate.is_active:
            AffiliateRepository.create_affiliate_error_log(
                db,
                order_id=order.id,
                affiliate_code=affiliate_code,
                error_type="INACTIVE_AFFILIATE",
                error_message="Affiliate is inactive",
            )
            return None

        # 5. 유효한 Affiliate ID 반환
        return affiliate.id
