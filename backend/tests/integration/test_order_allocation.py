"""주문 할당 - 통합 테스트 (TDD)"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from src.persistence.models import (
    Order,
    OrderItem,
    FulfillmentPartner,
    PartnerAllocatedInventory,
    ShipmentAllocation,
)
from src.utils.exceptions import OrderException


class TestOrderAllocationIntegration:
    """주문 할당 통합 테스트"""

    @pytest.fixture
    def partner_a(self, test_db: Session):
        """배송담당자 A (3일 전 할당)"""
        partner = FulfillmentPartner(
            name="Partner A",
            email="partner_a_alloc@example.com",
            is_active=True,
            last_allocated_at=datetime.utcnow() - timedelta(days=3),
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)
        return partner

    @pytest.fixture
    def partner_b(self, test_db: Session):
        """배송담당자 B (1일 전 할당)"""
        partner = FulfillmentPartner(
            name="Partner B",
            email="partner_b_alloc@example.com",
            is_active=True,
            last_allocated_at=datetime.utcnow() - timedelta(days=1),
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)
        return partner

    @pytest.fixture
    def setup_inventories_20_total(self, test_db: Session, partner_a, partner_b, sample_product):
        """전체 재고 20개 설정 (A: 15개, B: 5개)"""
        inv_a = PartnerAllocatedInventory(
            partner_id=partner_a.id,
            product_id=sample_product.id,
            allocated_quantity=15,
            remaining_quantity=15,
            stock_version=0,
        )
        inv_b = PartnerAllocatedInventory(
            partner_id=partner_b.id,
            product_id=sample_product.id,
            allocated_quantity=5,
            remaining_quantity=5,
            stock_version=0,
        )
        test_db.add_all([inv_a, inv_b])
        test_db.commit()
        test_db.refresh(inv_a)
        test_db.refresh(inv_b)
        return {"partner_a": partner_a, "partner_b": partner_b, "inv_a": inv_a, "inv_b": inv_b}

    def _create_order_with_item(
        self, test_db: Session, sample_customer, sample_product, quantity: int
    ) -> tuple:
        """주문 및 주문 상품 생성 헬퍼"""
        order = Order(
            order_number=f"ORD-TEST-{datetime.utcnow().timestamp()}",
            customer_id=sample_customer.id,
            subtotal=Decimal(str(sample_product.price * quantity)),
            shipping_fee=Decimal("100.00"),
            total_price=Decimal(str(sample_product.price * quantity + 100)),
            status="pending",
            fulfillment_partner_id=None,
        )
        test_db.add(order)
        test_db.commit()
        test_db.refresh(order)

        order_item = OrderItem(
            order_id=order.id,
            product_id=sample_product.id,
            quantity=quantity,
            unit_price=sample_product.price,
        )
        test_db.add(order_item)
        test_db.commit()
        test_db.refresh(order_item)

        return order, order_item

    # ========== TC-4.3.1: 주문 할당 성공 (1순위 배송담당자 재고 충분) ==========
    def test_order_allocation_success_with_first_partner(
        self, test_db: Session, sample_customer, sample_product, setup_inventories_20_total
    ):
        """
        TC-4.3.1: 주문 할당 성공 (1순위 배송담당자 재고 충분) 🟢 Happy 🟠 Integration

        Given:
        - Order 생성 (status=pending, fulfillment_partner_id=NULL)
        - 배송담당자 A (last_allocated_at: 3일 전, 재고 15개)
        - 배송담당자 B (last_allocated_at: 1일 전, 재고 5개)
        - 주문: 상품 × 10개

        When:
        - allocate_order_to_partner() 호출

        Then:
        - fulfillment_partner_id = Partner A
        - ShipmentAllocation 생성
        - 재고 차감 (A: 15→5)
        - last_allocated_at 업데이트
        """
        setup = setup_inventories_20_total
        partner_a = setup["partner_a"]
        inv_a = setup["inv_a"]

        # Given: 주문 생성
        order, order_item = self._create_order_with_item(test_db, sample_customer, sample_product, 10)

        # When: 주문 할당
        from src.workflow.services.fulfillment_service import FulfillmentService

        result = FulfillmentService.allocate_order_to_partner(
            test_db,
            order_id=order.id,
        )

        # Then: 할당 성공
        assert result["success"] is True
        assert result["fulfillment_partner_id"] == partner_a.id

        # Order 검증
        test_db.refresh(order)
        assert order.fulfillment_partner_id == partner_a.id

        # ShipmentAllocation 검증
        allocations = test_db.query(ShipmentAllocation).filter(
            ShipmentAllocation.order_id == order.id
        ).all()
        assert len(allocations) == 1
        assert allocations[0].partner_id == partner_a.id
        assert allocations[0].quantity == 10

        # 재고 검증
        test_db.refresh(inv_a)
        assert inv_a.remaining_quantity == 5  # 15 - 10
        assert inv_a.stock_version == 1

        # last_allocated_at 업데이트 확인
        test_db.refresh(partner_a)
        assert partner_a.last_allocated_at is not None

    # ========== TC-4.3.2: 주문 할당 성공 (1순위 재고 부족, 2순위로 재할당) ==========
    def test_order_allocation_success_with_second_partner(
        self, test_db: Session, sample_customer, sample_product, partner_a, partner_b
    ):
        """
        TC-4.3.2: 주문 할당 성공 (1순위 재고 부족, 2순위로 재할당) 🟨 Edge 🟠 Integration

        Given:
        - Order: 주문량 12개
        - 배송담당자 A (last_allocated_at: 3일 전, 재고 8개) - 1순위
        - 배송담당자 B (last_allocated_at: 1일 전, 재고 12개) - 2순위
        - 전체 재고: 20개

        When:
        - allocate_order_to_partner() 호출

        Then:
        - 1순위 A 재고 부족 → 2순위 B로 할당
        - fulfillment_partner_id = Partner B
        - ShipmentAllocation 생성
        - 재고 차감 (B: 12→0)
        - last_allocated_at 업데이트 (B만)
        """
        # Given: 재고 설정 (A: 8개, B: 12개)
        inv_a = PartnerAllocatedInventory(
            partner_id=partner_a.id,
            product_id=sample_product.id,
            allocated_quantity=8,
            remaining_quantity=8,
            stock_version=0,
        )
        inv_b = PartnerAllocatedInventory(
            partner_id=partner_b.id,
            product_id=sample_product.id,
            allocated_quantity=12,
            remaining_quantity=12,
            stock_version=0,
        )
        test_db.add_all([inv_a, inv_b])
        test_db.commit()
        test_db.refresh(inv_a)
        test_db.refresh(inv_b)

        # 주문 생성
        order, order_item = self._create_order_with_item(test_db, sample_customer, sample_product, 12)

        # When: 주문 할당
        from src.workflow.services.fulfillment_service import FulfillmentService

        result = FulfillmentService.allocate_order_to_partner(
            test_db,
            order_id=order.id,
        )

        # Then: 2순위 B로 할당
        assert result["success"] is True
        assert result["fulfillment_partner_id"] == partner_b.id

        # Order 검증
        test_db.refresh(order)
        assert order.fulfillment_partner_id == partner_b.id

        # ShipmentAllocation 검증
        allocations = test_db.query(ShipmentAllocation).filter(
            ShipmentAllocation.order_id == order.id
        ).all()
        assert len(allocations) == 1
        assert allocations[0].partner_id == partner_b.id

        # 재고 검증 (B: 12→0)
        test_db.refresh(inv_b)
        assert inv_b.remaining_quantity == 0
        assert inv_b.stock_version == 1

        # A는 미변경
        test_db.refresh(inv_a)
        assert inv_a.remaining_quantity == 8
        assert inv_a.stock_version == 0

    # ========== TC-4.3.3: 전체 재고 부족 ==========
    def test_order_allocation_insufficient_total_stock(
        self, test_db: Session, sample_customer, sample_product, partner_a, partner_b
    ):
        """
        TC-4.3.3: 전체 재고 부족 🔴 Error 🟠 Integration

        Given:
        - Order: 주문량 25개
        - 전체 배송담당자 재고: 20개 (부족)

        When:
        - allocate_order_to_partner() 호출

        Then:
        - InsufficientInventoryError 발생
        - Order 미변경 (fulfillment_partner_id=NULL)
        - ShipmentAllocation 미생성
        """
        # Given: 재고 설정 (전체 20개)
        inv_a = PartnerAllocatedInventory(
            partner_id=partner_a.id,
            product_id=sample_product.id,
            allocated_quantity=12,
            remaining_quantity=12,
            stock_version=0,
        )
        inv_b = PartnerAllocatedInventory(
            partner_id=partner_b.id,
            product_id=sample_product.id,
            allocated_quantity=8,
            remaining_quantity=8,
            stock_version=0,
        )
        test_db.add_all([inv_a, inv_b])
        test_db.commit()

        # 주문 생성 (25개 - 부족)
        order, order_item = self._create_order_with_item(test_db, sample_customer, sample_product, 25)

        # When & Then: 재고 부족 에러
        from src.workflow.services.fulfillment_service import FulfillmentService

        with pytest.raises(OrderException) as exc_info:
            FulfillmentService.allocate_order_to_partner(test_db, order_id=order.id)

        assert exc_info.value.code == "INSUFFICIENT_STOCK"

        # Order 미변경
        test_db.refresh(order)
        assert order.fulfillment_partner_id is None

        # ShipmentAllocation 미생성
        allocations = test_db.query(ShipmentAllocation).filter(
            ShipmentAllocation.order_id == order.id
        ).all()
        assert len(allocations) == 0

    # ========== TC-4.3.4: 모든 배송담당자 재고 부족 ==========
    def test_order_allocation_all_partners_insufficient_stock(
        self, test_db: Session, sample_customer, sample_product, partner_a, partner_b
    ):
        """
        TC-4.3.4: 모든 배송담당자 재고 부족 🔴 Error 🟠 Integration

        Given:
        - Order: 주문량 15개
        - 배송담당자 A (재고 8개)
        - 배송담당자 B (재고 7개)
        - 전체: 15개 (정확히 필요량이지만 어느 배송담당자도 단독으로 충분하지 않음)

        When:
        - allocate_order_to_partner() 호출

        Then:
        - 1순위 A: 8개 < 15개 (부족)
        - 2순위 B: 7개 < 15개 (부족)
        - AllPartnersInsufficientInventoryError 발생
        - Order 미변경
        - ShipmentAllocation 미생성
        """
        # Given: 재고 설정 (A: 8개, B: 7개)
        inv_a = PartnerAllocatedInventory(
            partner_id=partner_a.id,
            product_id=sample_product.id,
            allocated_quantity=8,
            remaining_quantity=8,
            stock_version=0,
        )
        inv_b = PartnerAllocatedInventory(
            partner_id=partner_b.id,
            product_id=sample_product.id,
            allocated_quantity=7,
            remaining_quantity=7,
            stock_version=0,
        )
        test_db.add_all([inv_a, inv_b])
        test_db.commit()

        # 주문 생성 (15개)
        order, order_item = self._create_order_with_item(test_db, sample_customer, sample_product, 15)

        # When & Then: 모든 배송담당자 재고 부족
        from src.workflow.services.fulfillment_service import FulfillmentService

        with pytest.raises(OrderException) as exc_info:
            FulfillmentService.allocate_order_to_partner(test_db, order_id=order.id)

        assert exc_info.value.code == "ALL_PARTNERS_INSUFFICIENT_STOCK"

        # Order 미변경
        test_db.refresh(order)
        assert order.fulfillment_partner_id is None

        # ShipmentAllocation 미생성
        allocations = test_db.query(ShipmentAllocation).filter(
            ShipmentAllocation.order_id == order.id
        ).all()
        assert len(allocations) == 0
