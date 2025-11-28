"""재고 관련 데이터 접근 계층"""

from uuid import UUID
from sqlalchemy.orm import Session

from src.persistence.models import PartnerAllocatedInventory


class InventoryRepository:
    """Inventory Repository"""

    @staticmethod
    def get_total_available_quantity(db: Session, product_id: UUID) -> int:
        """상품의 총 가용 재고 조회"""
        inventory_records = db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.product_id == product_id
        ).all()

        total = sum(record.remaining_quantity for record in inventory_records)
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
    ) -> PartnerAllocatedInventory:
        """배송담당자별 상품 재고 조회"""
        return db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.partner_id == partner_id,
            PartnerAllocatedInventory.product_id == product_id,
        ).first()

    @staticmethod
    def get_all_partner_inventory_for_product(
        db: Session,
        product_id: UUID,
    ):
        """상품의 모든 배송담당자별 재고 조회"""
        return db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.product_id == product_id
        ).all()
