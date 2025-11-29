"""재고 관련 데이터 접근 계층"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import PartnerAllocatedInventory
from src.utils.exceptions import OrderException


class InventoryRepository:
    """Inventory Repository"""

    @staticmethod
    def get_total_available_quantity(db: Session, product_id: UUID) -> int:
        """상품의 총 가용 재고 조회"""
        inventory_records = db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.product_id == product_id
        ).all()

        total: int = sum((record.remaining_quantity for record in inventory_records), 0)
        return total

    @staticmethod
    def check_inventory_available(db: Session, product_id: UUID, quantity: int) -> bool:
        """재고 가용성 확인"""
        total_available = InventoryRepository.get_total_available_quantity(db, product_id)
        return total_available >= quantity

    @staticmethod
    def get_partner_inventory(
        db: Session,
        partner_id: UUID,
        product_id: UUID,
    ) -> Optional[PartnerAllocatedInventory]:
        """배송담당자별 상품 재고 조회"""
        return db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.partner_id == partner_id,
            PartnerAllocatedInventory.product_id == product_id,
        ).first()

    @staticmethod
    def get_all_partner_inventory_for_product(
        db: Session,
        product_id: UUID,
    ) -> list[PartnerAllocatedInventory]:
        """상품의 모든 배송담당자별 재고 조회"""
        return db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.product_id == product_id
        ).all()

    @staticmethod
    def decrease_inventory_with_optimistic_lock(
        db: Session,
        inventory_id: UUID,
        quantity: int,
        max_retries: int = 3,
    ) -> dict[str, bool | int]:
        """
        낙관적 락을 사용한 재고 차감

        Args:
            db: 데이터베이스 세션
            inventory_id: PartnerAllocatedInventory ID
            quantity: 차감할 수량
            max_retries: 최대 재시도 횟수

        Returns:
            {
                "success": bool,
                "remaining_quantity": int,
                "new_stock_version": int,
            }

        Raises:
            OrderException: 재고 부족 또는 재시도 초과
        """
        for attempt in range(max_retries):
            # 1. 현재 재고 조회
            inventory = db.query(PartnerAllocatedInventory).filter(
                PartnerAllocatedInventory.id == inventory_id
            ).first()

            if not inventory:
                raise OrderException(
                    code="INVENTORY_NOT_FOUND",
                    message=f"재고를 찾을 수 없습니다: {inventory_id}",
                )

            # 2. 재고 확인
            if inventory.remaining_quantity < quantity:
                raise OrderException(
                    code="INSUFFICIENT_STOCK",
                    message=f"재고가 부족합니다. 보유: {inventory.remaining_quantity}, 필요: {quantity}",
                )

            # 3. 낙관적 락으로 UPDATE
            current_version = inventory.stock_version
            new_remaining = inventory.remaining_quantity - quantity
            new_version = current_version + 1

            updated_rows = db.query(PartnerAllocatedInventory).filter(
                PartnerAllocatedInventory.id == inventory_id,
                PartnerAllocatedInventory.stock_version == current_version,
            ).update({
                PartnerAllocatedInventory.remaining_quantity: new_remaining,
                PartnerAllocatedInventory.stock_version: new_version,
            })

            db.commit()

            # 4. UPDATE 성공 확인
            if updated_rows > 0:
                return {
                    "success": True,
                    "remaining_quantity": new_remaining,
                    "new_stock_version": new_version,
                }

            # 5. UPDATE 실패 → 재시도

        # 6. 재시도 초과
        raise OrderException(
            code="OPTIMISTIC_LOCK_FAILED",
            message=f"재고 업데이트에 실패했습니다. {max_retries}회 재시도 후 포기: {inventory_id}",
        )
