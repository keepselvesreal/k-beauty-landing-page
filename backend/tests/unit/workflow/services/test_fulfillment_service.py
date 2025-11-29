"""배송담당자 일괄 정렬 - 단위 테스트 (TDD)"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.persistence.models import (
    FulfillmentPartner,
    PartnerAllocatedInventory,
)


class TestGetSortedPartnersForAllocation:
    """배송담당자 일괄 정렬 테스트"""

    @pytest.fixture
    def partner_a(self, test_db: Session):
        """배송담당자 A (older last_allocated_at)"""
        partner = FulfillmentPartner(
            name="Partner A",
            email="partner_a@example.com",
            is_active=True,
            last_allocated_at=datetime.utcnow() - timedelta(days=2),  # 2025-11-27
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)
        return partner

    @pytest.fixture
    def partner_b(self, test_db: Session):
        """배송담당자 B (newer last_allocated_at)"""
        partner = FulfillmentPartner(
            name="Partner B",
            email="partner_b@example.com",
            is_active=True,
            last_allocated_at=datetime.utcnow() - timedelta(days=1),  # 2025-11-28
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)
        return partner

    @pytest.fixture
    def partner_c(self, test_db: Session):
        """배송담당자 C (newest last_allocated_at)"""
        partner = FulfillmentPartner(
            name="Partner C",
            email="partner_c@example.com",
            is_active=True,
            last_allocated_at=datetime.utcnow(),  # 2025-11-29
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)
        return partner

    @pytest.fixture
    def new_partner_no_allocation(self, test_db: Session):
        """할당받지 않은 새로운 배송담당자 (NULL last_allocated_at)"""
        partner = FulfillmentPartner(
            name="New Partner",
            email="new_partner@example.com",
            is_active=True,
            last_allocated_at=None,
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)
        return partner

    # ========== TC-4.1.1: 정상 정렬 ==========
    def test_sort_partners_by_last_allocated_at(
        self, test_db: Session, sample_product, partner_a, partner_b, partner_c
    ):
        """
        TC-4.1.1: 정상 정렬 (last_allocated_at 기준) 🟢 Happy 🔵 Unit

        Given:
        - 3명의 배송담당자, 모두 is_active=True
        - Partner A: last_allocated_at=2025-11-27
        - Partner B: last_allocated_at=2025-11-28 10:00
        - Partner C: last_allocated_at=2025-11-28 14:00

        When:
        - get_sorted_partners_for_allocation(product_id) 호출

        Then:
        - 반환 순서: [Partner A, Partner B, Partner C]
        - (가장 오래전에 할당받은 A가 1순위)
        """
        # Given: 재고 할당
        for partner, remaining_qty in [(partner_a, 50), (partner_b, 60), (partner_c, 40)]:
            inventory = PartnerAllocatedInventory(
                partner_id=partner.id,
                product_id=sample_product.id,
                allocated_quantity=100,
                remaining_quantity=remaining_qty,
                stock_version=0,
            )
            test_db.add(inventory)
        test_db.commit()

        # When: 정렬 실행
        from src.workflow.services.fulfillment_service import FulfillmentService
        sorted_partners = FulfillmentService.get_sorted_partners_for_allocation(
            test_db, sample_product.id
        )

        # Then: 순서 검증
        assert len(sorted_partners) == 3
        assert sorted_partners[0].id == partner_a.id
        assert sorted_partners[1].id == partner_b.id
        assert sorted_partners[2].id == partner_c.id

    # ========== TC-4.1.2: last_allocated_at이 같을 때 remaining_quantity로 정렬 ==========
    def test_sort_partners_by_remaining_quantity_when_same_last_allocated_at(
        self, test_db: Session, sample_product
    ):
        """
        TC-4.1.2: last_allocated_at이 같을 때 remaining_quantity로 정렬 🟨 Edge 🔵 Unit

        Given:
        - 2명의 배송담당자, 모두 is_active=True
        - 동일한 last_allocated_at
        - Partner A: remaining_quantity=30
        - Partner B: remaining_quantity=70

        When:
        - 정렬 실행

        Then:
        - 반환 순서: [Partner B, Partner A]
        - (remaining_quantity가 많은 B가 먼저)
        """
        same_time = datetime.utcnow() - timedelta(days=1)

        partner_a = FulfillmentPartner(
            name="Partner A",
            email="same_time_a@example.com",
            is_active=True,
            last_allocated_at=same_time,
        )
        partner_b = FulfillmentPartner(
            name="Partner B",
            email="same_time_b@example.com",
            is_active=True,
            last_allocated_at=same_time,
        )
        test_db.add_all([partner_a, partner_b])
        test_db.commit()

        # Given: 재고 할당 (remaining_quantity 다름)
        inv_a = PartnerAllocatedInventory(
            partner_id=partner_a.id,
            product_id=sample_product.id,
            allocated_quantity=50,
            remaining_quantity=30,
            stock_version=0,
        )
        inv_b = PartnerAllocatedInventory(
            partner_id=partner_b.id,
            product_id=sample_product.id,
            allocated_quantity=100,
            remaining_quantity=70,
            stock_version=0,
        )
        test_db.add_all([inv_a, inv_b])
        test_db.commit()

        # When: 정렬 실행
        from src.workflow.services.fulfillment_service import FulfillmentService
        sorted_partners = FulfillmentService.get_sorted_partners_for_allocation(
            test_db, sample_product.id
        )

        # Then: remaining_quantity 많은 순
        assert len(sorted_partners) == 2
        assert sorted_partners[0].id == partner_b.id  # remaining=70
        assert sorted_partners[1].id == partner_a.id  # remaining=30

    # ========== TC-4.1.3: is_active=False인 배송담당자는 제외 ==========
    def test_exclude_inactive_partners(
        self, test_db: Session, sample_product, partner_a, partner_b, inactive_partner
    ):
        """
        TC-4.1.3: is_active=False인 배송담당자는 제외 🟢 Happy 🔵 Unit

        Given:
        - Partner A: is_active=True, last_allocated_at=2025-11-27
        - Partner B: is_active=True, last_allocated_at=2025-11-28
        - Inactive: is_active=False, last_allocated_at=2025-11-26 (더 오래됨)

        When:
        - 정렬 실행

        Then:
        - 반환 리스트: [Partner A, Partner B]
        - Inactive는 제외됨
        """
        # Given: 재고 할당 (모든 파트너)
        for partner in [partner_a, partner_b, inactive_partner]:
            inventory = PartnerAllocatedInventory(
                partner_id=partner.id,
                product_id=sample_product.id,
                allocated_quantity=100,
                remaining_quantity=50,
                stock_version=0,
            )
            test_db.add(inventory)
        test_db.commit()

        # When: 정렬 실행
        from src.workflow.services.fulfillment_service import FulfillmentService
        sorted_partners = FulfillmentService.get_sorted_partners_for_allocation(
            test_db, sample_product.id
        )

        # Then: 활성 파트너만 포함
        assert len(sorted_partners) == 2
        assert all(p.is_active for p in sorted_partners)
        assert inactive_partner.id not in [p.id for p in sorted_partners]

    # ========== TC-4.1.4: last_allocated_at이 NULL인 경우 ==========
    def test_null_last_allocated_at_treated_as_oldest(
        self, test_db: Session, sample_product, partner_b, new_partner_no_allocation
    ):
        """
        TC-4.1.4: last_allocated_at이 NULL인 경우 처리 🟨 Edge 🔵 Unit

        Given:
        - Partner with NULL: last_allocated_at=NULL, remaining_quantity=50
        - Partner B: last_allocated_at=2025-11-28, remaining_quantity=60

        When:
        - 정렬 실행

        Then:
        - 반환 순서: [new_partner_no_allocation, Partner B]
        - (NULL을 가장 오래된 것으로 간주)
        """
        # Given: 재고 할당
        inv_new = PartnerAllocatedInventory(
            partner_id=new_partner_no_allocation.id,
            product_id=sample_product.id,
            allocated_quantity=100,
            remaining_quantity=50,
            stock_version=0,
        )
        inv_b = PartnerAllocatedInventory(
            partner_id=partner_b.id,
            product_id=sample_product.id,
            allocated_quantity=100,
            remaining_quantity=60,
            stock_version=0,
        )
        test_db.add_all([inv_new, inv_b])
        test_db.commit()

        # When: 정렬 실행
        from src.workflow.services.fulfillment_service import FulfillmentService
        sorted_partners = FulfillmentService.get_sorted_partners_for_allocation(
            test_db, sample_product.id
        )

        # Then: NULL이 가장 먼저
        assert len(sorted_partners) == 2
        assert sorted_partners[0].id == new_partner_no_allocation.id  # NULL이 1순위
        assert sorted_partners[1].id == partner_b.id

    # ========== TC-4.1.5: 유효한 배송담당자가 없는 경우 ==========
    def test_no_active_partners_available(self, test_db: Session, sample_product):
        """
        TC-4.1.5: 유효한 배송담당자가 없는 경우 🔴 Error 🔵 Unit

        Given:
        - 상품 A에 할당된 배송담당자가 없음

        When:
        - 정렬 실행

        Then:
        - 빈 리스트 반환
        """
        # When: 정렬 실행 (데이터 없음)
        from src.workflow.services.fulfillment_service import FulfillmentService
        sorted_partners = FulfillmentService.get_sorted_partners_for_allocation(
            test_db, sample_product.id
        )

        # Then: 빈 리스트
        assert sorted_partners == []
