"""어필리에이트 비즈니스 로직 서비스"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import Order, Settings
from src.persistence.repositories.affiliate_repository import AffiliateRepository


class AffiliateService:
    """Affiliate Service"""

    @staticmethod
    def calculate_marketing_commission(profit_per_unit: Decimal, commission_rate: Decimal, quantity: int) -> Decimal:
        """마케팅 커미션 계산

        Args:
            profit_per_unit: 상품 1개당 순이윤
            commission_rate: 마케팅 커미션율 (0.2 = 20%)
            quantity: 주문 수량

        Returns:
            계산된 마케팅 커미션 금액
        """
        return profit_per_unit * commission_rate * quantity

    @staticmethod
    def record_marketing_commission_if_applicable(db: Session, order: Order) -> None:
        """주문에 대한 마케팅 커미션 기록 (인플루언서가 있는 경우만)

        Args:
            db: 데이터베이스 세션
            order: 주문 객체

        Returns:
            None
        """
        # 1. 마케팅 인플루언서가 없으면 기록하지 않음
        if not order.marketing_affiliate_id:
            return

        # 2. Settings에서 마케팅 커미션율 조회
        settings = db.query(Settings).first()
        if not settings:
            return

        # 3. 주문의 OrderItem 조회하여 수량 계산
        from src.persistence.models import OrderItem
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
        if not order_items:
            return

        total_quantity = sum(item.quantity for item in order_items)

        # 4. 마케팅 커미션 계산
        marketing_commission = AffiliateService.calculate_marketing_commission(
            order_items[0].profit_per_item,  # profit_per_item 사용
            settings.marketing_commission_rate,
            total_quantity,
        )

        # 5. Order에 마케팅 커미션 저장
        order.marketing_commission = marketing_commission

        # 6. Affiliate Sale 기록
        AffiliateRepository.create_affiliate_sale(
            db,
            affiliate_id=order.marketing_affiliate_id,
            order_id=order.id,
            marketing_commission=marketing_commission,
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
