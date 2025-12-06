"""재고 관련 데이터 접근 계층"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.persistence.models import (
    PartnerAllocatedInventory,
    InventoryAdjustmentLog,
    FulfillmentPartner,
    Product,
)
from src.workflow.exceptions import OrderException


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

    @staticmethod
    def get_all_inventory_by_admin(db: Session) -> list[dict]:
        """
        모든 배송담당자별 재고 조회 (관리자용)

        Returns:
            [
                {
                    "inventory_id": UUID,
                    "partner_id": UUID,
                    "partner_name": str,
                    "product_id": UUID,
                    "product_name": str,
                    "current_quantity": int,
                    "allocated_quantity": int,
                    "last_adjusted_at": datetime,
                }
            ]
        """
        results = db.query(
            PartnerAllocatedInventory.id.label("inventory_id"),
            PartnerAllocatedInventory.partner_id,
            FulfillmentPartner.name.label("partner_name"),
            PartnerAllocatedInventory.product_id,
            Product.name.label("product_name"),
            PartnerAllocatedInventory.remaining_quantity.label("current_quantity"),
            PartnerAllocatedInventory.allocated_quantity,
            PartnerAllocatedInventory.updated_at.label("last_adjusted_at"),
        ).join(
            FulfillmentPartner, PartnerAllocatedInventory.partner_id == FulfillmentPartner.id
        ).join(
            Product, PartnerAllocatedInventory.product_id == Product.id
        ).order_by(
            FulfillmentPartner.name,
            Product.name,
        ).all()

        return [dict(row._mapping) for row in results]

    @staticmethod
    def get_inventory_adjustment_history(
        db: Session,
        inventory_id: UUID,
        limit: int = 10,
    ) -> list[dict]:
        """
        특정 재고의 조정 이력 조회

        Args:
            db: 데이터베이스 세션
            inventory_id: PartnerAllocatedInventory ID
            limit: 조회 건수 (기본값 10)

        Returns:
            [
                {
                    "log_id": UUID,
                    "old_quantity": int,
                    "new_quantity": int,
                    "reason": str | None,
                    "adjusted_at": datetime,
                    "adjusted_by": str,  # admin email
                }
            ]
        """
        results = db.query(
            InventoryAdjustmentLog.id.label("log_id"),
            InventoryAdjustmentLog.old_quantity,
            InventoryAdjustmentLog.new_quantity,
            InventoryAdjustmentLog.reason,
            InventoryAdjustmentLog.created_at.label("adjusted_at"),
        ).filter(
            InventoryAdjustmentLog.inventory_id == inventory_id
        ).order_by(
            InventoryAdjustmentLog.created_at.desc()
        ).limit(limit).all()

        return [dict(row._mapping) for row in results]

    @staticmethod
    def adjust_inventory(
        db: Session,
        inventory_id: UUID,
        new_quantity: int,
        admin_id: UUID,
        reason: Optional[str] = None,
    ) -> dict:
        """
        재고 수량 수동 조정 및 이력 기록

        Args:
            db: 데이터베이스 세션
            inventory_id: PartnerAllocatedInventory ID
            new_quantity: 새로운 수량
            admin_id: 관리자 User ID
            reason: 조정 사유 (선택적)

        Returns:
            {
                "inventory_id": UUID,
                "old_quantity": int,
                "new_quantity": int,
                "log_id": UUID,
                "updated_at": datetime,
            }

        Raises:
            OrderException: 재고를 찾을 수 없거나 유효성 검사 실패
        """
        # 1. 재고 조회
        inventory = db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.id == inventory_id
        ).first()

        if not inventory:
            raise OrderException(
                code="INVENTORY_NOT_FOUND",
                message=f"재고를 찾을 수 없습니다: {inventory_id}",
            )

        # 2. 유효성 검사
        if new_quantity < 0:
            raise OrderException(
                code="INVALID_QUANTITY",
                message="재고 수량은 음수일 수 없습니다",
            )

        old_quantity = inventory.remaining_quantity

        # 3. 재고 업데이트 (트랜잭션)
        try:
            inventory.remaining_quantity = new_quantity
            db.flush()  # 업데이트 먼저 처리

            # 4. 이력 기록 생성
            adjustment_log = InventoryAdjustmentLog(
                inventory_id=inventory_id,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                adjusted_by=admin_id,
                reason=reason,
            )
            db.add(adjustment_log)

            # 5. 커밋
            db.commit()

            return {
                "inventory_id": inventory_id,
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "log_id": adjustment_log.id,
                "updated_at": inventory.updated_at,
            }

        except Exception as e:
            db.rollback()
            raise OrderException(
                code="INVENTORY_UPDATE_FAILED",
                message=f"재고 업데이트 중 오류 발생: {str(e)}",
            )
