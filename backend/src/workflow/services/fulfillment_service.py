"""배송담당자 할당 관련 비즈니스 로직"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import case
from sqlalchemy.orm import Session

from src.persistence.models import (
    FulfillmentPartner,
    Order,
    OrderItem,
    PartnerAllocatedInventory,
    ShipmentAllocation,
)
from src.persistence.repositories.inventory_repository import InventoryRepository
from src.utils.exceptions import OrderException


class FulfillmentService:
    """배송담당자 할당 관련 비즈니스 로직"""

    @staticmethod
    def get_sorted_partners_for_allocation(
        db: Session,
        product_id: UUID,
    ) -> List[FulfillmentPartner]:
        """
        배송담당자를 라운드 로빈 기준으로 정렬

        정렬 기준:
        1. is_active=True만 대상
        2. last_allocated_at 오래된 순 (NULL을 가장 오래된 것으로 간주)
        3. 같으면 remaining_quantity 많은 순

        Args:
            db: 데이터베이스 세션
            product_id: 상품 ID

        Returns:
            정렬된 FulfillmentPartner 리스트
        """
        # 서브쿼리: 해당 product_id의 partner별 재고 조회
        partner_inventory = db.query(
            PartnerAllocatedInventory.partner_id,
            PartnerAllocatedInventory.remaining_quantity
        ).filter(
            PartnerAllocatedInventory.product_id == product_id
        ).subquery()

        # FulfillmentPartner 정렬
        partners = db.query(FulfillmentPartner).join(
            partner_inventory,
            FulfillmentPartner.id == partner_inventory.c.partner_id
        ).filter(
            FulfillmentPartner.is_active,
        ).order_by(
            # NULL을 가장 오래된 것으로 간주 (NULL = False = 0)
            case(
                (FulfillmentPartner.last_allocated_at.is_(None), 0),
                else_=1
            ).asc(),
            # last_allocated_at이 오래된 순
            FulfillmentPartner.last_allocated_at.asc(),
            # remaining_quantity가 많은 순
            partner_inventory.c.remaining_quantity.desc(),
        ).all()

        return partners

    @staticmethod
    def allocate_order_to_partner(
        db: Session,
        order_id: UUID,
    ) -> dict[str, bool | UUID | int]:
        """
        주문을 배송담당자에게 할당

        단계:
        1. Order와 OrderItem 조회
        2. 필요한 총 수량 계산
        3. 전체 재고 확인
        4. 배송담당자 정렬 (라운드 로빈)
        5. 첫 번째 재고 충분한 배송담당자 선택
        6. 재고 차감 (낙관적 락)
        7. ShipmentAllocation 생성
        8. Order와 Partner 업데이트

        Args:
            db: 데이터베이스 세션
            order_id: Order ID

        Returns:
            {
                "success": bool,
                "fulfillment_partner_id": UUID,
                "allocated_quantity": int,
            }

        Raises:
            OrderException: 재고 부족 또는 주문 없음
        """
        # 1. Order 조회
        order: Optional[Order] = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise OrderException(
                code="ORDER_NOT_FOUND",
                message=f"주문을 찾을 수 없습니다: {order_id}",
            )

        # 2. OrderItem 조회 및 필요 수량 계산
        order_items: list[OrderItem] = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        if not order_items:
            raise OrderException(
                code="ORDER_ITEM_NOT_FOUND",
                message=f"주문 상품을 찾을 수 없습니다: {order_id}",
            )

        total_quantity: int = sum((item.quantity for item in order_items), 0)

        # 3. 각 상품별 전체 재고 확인 (단일 상품이라고 가정)
        product_id: UUID = order_items[0].product_id  # type: ignore
        total_available: int = InventoryRepository.get_total_available_quantity(db, product_id)

        if total_available < total_quantity:
            raise OrderException(
                code="INSUFFICIENT_STOCK",
                message=f"전체 재고 부족: 보유 {total_available}, 필요 {total_quantity}",
            )

        # 4. 배송담당자 정렬 (라운드 로빈)
        sorted_partners: List[FulfillmentPartner] = FulfillmentService.get_sorted_partners_for_allocation(
            db, product_id
        )

        if not sorted_partners:
            raise OrderException(
                code="NO_ACTIVE_PARTNERS",
                message="활성 배송담당자가 없습니다",
            )

        # 5. 첫 번째 재고 충분한 배송담당자 찾기
        selected_partner: Optional[FulfillmentPartner] = None
        selected_inventory: Optional[PartnerAllocatedInventory] = None
        for partner in sorted_partners:
            partner_inventory: Optional[PartnerAllocatedInventory] = db.query(PartnerAllocatedInventory).filter(
                PartnerAllocatedInventory.partner_id == partner.id,
                PartnerAllocatedInventory.product_id == product_id,
            ).first()

            if partner_inventory and partner_inventory.remaining_quantity >= total_quantity:
                selected_partner = partner
                selected_inventory = partner_inventory
                break

        if not selected_partner or not selected_inventory:
            raise OrderException(
                code="ALL_PARTNERS_INSUFFICIENT_STOCK",
                message="모든 배송담당자의 재고가 부족합니다",
            )

        # 6. 재고 차감 (낙관적 락)
        try:
            InventoryRepository.decrease_inventory_with_optimistic_lock(
                db,
                inventory_id=selected_inventory.id,
                quantity=total_quantity,
                max_retries=3,
            )
        except OrderException:
            # 재고 차감 실패 → 재시도 로직 (다른 배송담당자로)
            raise

        # 7. ShipmentAllocation 생성 (각 OrderItem마다)
        for order_item in order_items:
            allocation = ShipmentAllocation(
                order_id=order.id,
                order_item_id=order_item.id,
                partner_id=selected_partner.id,
                quantity=order_item.quantity,
            )
            db.add(allocation)

        db.commit()

        # 8. Order 업데이트
        order.fulfillment_partner_id = selected_partner.id
        db.add(order)

        # 9. Partner의 last_allocated_at 업데이트
        selected_partner.last_allocated_at = datetime.utcnow()
        db.add(selected_partner)

        db.commit()

        return {
            "success": True,
            "fulfillment_partner_id": selected_partner.id,
            "allocated_quantity": total_quantity,
        }
