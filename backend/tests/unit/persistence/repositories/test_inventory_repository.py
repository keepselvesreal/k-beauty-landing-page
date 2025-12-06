"""낙관적 락으로 재고 차감 - 단위 테스트 (TDD)"""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import patch

from src.persistence.models import PartnerAllocatedInventory
from src.workflow.exceptions import OrderException


class TestDecreaseInventoryWithOptimisticLock:
    """낙관적 락으로 재고 차감 테스트"""

    @pytest.fixture
    def sample_inventory(self, test_db: Session, sample_partner, sample_product):
        """테스트용 배송담당자 재고 (전체 20개)"""
        inventory = PartnerAllocatedInventory(
            partner_id=sample_partner.id,
            product_id=sample_product.id,
            allocated_quantity=20,
            remaining_quantity=20,
            stock_version=0,
        )
        test_db.add(inventory)
        test_db.commit()
        test_db.refresh(inventory)
        return inventory

    # ========== TC-4.2.1: 정상적으로 재고 차감 ==========
    def test_decrease_inventory_success(
        self, test_db: Session, sample_inventory
    ):
        """
        TC-4.2.1: 정상적으로 재고 차감 🟢 Happy 🔵 Unit

        Given:
        - PartnerAllocatedInventory: remaining_quantity=20, stock_version=0

        When:
        - decrease_inventory_with_optimistic_lock(inventory_id, quantity=5) 호출

        Then:
        - remaining_quantity: 20 → 15
        - stock_version: 0 → 1
        - UPDATE 성공
        """
        from src.persistence.repositories.inventory_repository import InventoryRepository

        # When: 재고 차감
        result = InventoryRepository.decrease_inventory_with_optimistic_lock(
            test_db,
            inventory_id=sample_inventory.id,
            quantity=5,
        )

        # Then: 재고 차감 확인
        assert result["success"] is True
        assert result["remaining_quantity"] == 15
        assert result["new_stock_version"] == 1

        # DB 재확인
        test_db.refresh(sample_inventory)
        assert sample_inventory.remaining_quantity == 15
        assert sample_inventory.stock_version == 1

    # ========== TC-4.2.2: 전체 재고를 정확히 소진 ==========
    def test_decrease_inventory_exact_total_amount(
        self, test_db: Session, sample_inventory
    ):
        """
        TC-4.2.2: 전체 재고를 정확히 소진 🟨 Edge 🔵 Unit

        Given:
        - remaining_quantity=20, stock_version=0

        When:
        - 20개 차감 요청 (전체 소진)

        Then:
        - remaining_quantity: 20 → 0
        - stock_version: 0 → 1
        - 성공
        """
        from src.persistence.repositories.inventory_repository import InventoryRepository

        # When: 전체 재고 차감
        result = InventoryRepository.decrease_inventory_with_optimistic_lock(
            test_db,
            inventory_id=sample_inventory.id,
            quantity=20,
        )

        # Then: 0으로 차감 성공
        assert result["success"] is True
        assert result["remaining_quantity"] == 0
        assert result["new_stock_version"] == 1

        test_db.refresh(sample_inventory)
        assert sample_inventory.remaining_quantity == 0
        assert sample_inventory.stock_version == 1

    # ========== TC-4.2.3: 재고 부족 (부족량: 5개) ==========
    def test_decrease_inventory_insufficient_stock(
        self, test_db: Session, sample_inventory
    ):
        """
        TC-4.2.3: 재고 부족 (부족량: 5개) 🔴 Error 🔵 Unit

        Given:
        - remaining_quantity=20, stock_version=0

        When:
        - 25개 차감 요청 (필요량 > 보유량)

        Then:
        - InsufficientInventoryError 발생
        - 데이터베이스 미변경 (remaining_quantity=20, stock_version=0 유지)
        """
        from src.persistence.repositories.inventory_repository import InventoryRepository

        # When & Then: 재고 부족 에러
        with pytest.raises(OrderException) as exc_info:
            InventoryRepository.decrease_inventory_with_optimistic_lock(
                test_db,
                inventory_id=sample_inventory.id,
                quantity=25,
            )

        assert exc_info.value.code == "INSUFFICIENT_STOCK"

        # DB 미변경 확인
        test_db.refresh(sample_inventory)
        assert sample_inventory.remaining_quantity == 20
        assert sample_inventory.stock_version == 0

    # ========== TC-4.2.4: stock_version 불일치로 재시도 성공 ==========
    def test_decrease_inventory_optimistic_lock_retry_success(
        self, test_db: Session, sample_inventory
    ):
        """
        TC-4.2.4: stock_version 불일치로 재시도 성공 🟨 Edge 🔵 Unit

        Given:
        - 초기: stock_version=0, remaining_quantity=20
        - 첫 시도 전 다른 요청이 업데이트: stock_version=0→1, remaining_quantity=20→15 (5개 차감 후)

        When:
        - 10개 차감 요청 (최대 재시도=3)

        Then:
        - 1차 시도: stock_version=0 조건으로 UPDATE 실패
        - 2차 시도: 재읽음 후, stock_version=1로 UPDATE 성공
        - 최종 상태: remaining_quantity=5 (15-10), stock_version=2
        """
        from src.persistence.repositories.inventory_repository import InventoryRepository

        # Given: 수동으로 stock_version 업데이트 (다른 요청 시뮬레이션)
        test_db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.id == sample_inventory.id
        ).update({
            PartnerAllocatedInventory.remaining_quantity: 15,
            PartnerAllocatedInventory.stock_version: 1,
        })
        test_db.commit()

        # When: 차감 요청 (재시도 로직 포함)
        result = InventoryRepository.decrease_inventory_with_optimistic_lock(
            test_db,
            inventory_id=sample_inventory.id,
            quantity=10,
            max_retries=3,
        )

        # Then: 재시도 후 성공
        assert result["success"] is True
        assert result["remaining_quantity"] == 5  # 15 - 10
        assert result["new_stock_version"] == 2  # 1 + 1

        test_db.refresh(sample_inventory)
        assert sample_inventory.remaining_quantity == 5
        assert sample_inventory.stock_version == 2

    # ========== TC-4.2.5: 재시도 초과 ==========
    def test_decrease_inventory_optimistic_lock_max_retries_exceeded(
        self, test_db: Session, sample_inventory
    ):
        """
        TC-4.2.5: 재시도 초과 🔴 Error 🔵 Unit

        Given:
        - 초기: remaining_quantity=20, stock_version=0
        - 최대 재시도: 3회
        - 매 시도마다 다른 스레드가 stock_version을 변경 (지속적 충돌)

        When:
        - 차감 요청 실행

        Then:
        - 3회 재시도 후 OptimisticLockFailedError 발생
        """
        from src.persistence.repositories.inventory_repository import InventoryRepository

        # Given: .update() 메서드를 mock해서 항상 0 (실패)을 반환하도록
        # 이는 stock_version 불일치로 UPDATE가 0개 행을 반영하는 상황을 시뮬레이션
        with patch('sqlalchemy.orm.query.Query.update', return_value=0):
            # When & Then: 최대 재시도 초과
            with pytest.raises(OrderException) as exc_info:
                InventoryRepository.decrease_inventory_with_optimistic_lock(
                    test_db,
                    inventory_id=sample_inventory.id,
                    quantity=5,
                    max_retries=3,
                )

            assert exc_info.value.code == "OPTIMISTIC_LOCK_FAILED"

    # ========== TC-4.2.6: 동시 요청에서 낙관적 락 동시성 보장 ==========
    def test_decrease_inventory_concurrent_simulation(
        self, test_db: Session, sample_inventory
    ):
        """
        TC-4.2.6: 동시 요청에서 낙관적 락 동시성 보장 🟨 Edge 🔵 Unit

        Given:
        - 초기: remaining_quantity=20, stock_version=0
        - 첫 번째 요청: 15개 차감 후 stock_version=0→1로 업데이트됨 (시뮬레이션)
        - 두 번째 요청: 같은 inventory_id로 15개 차감 시도

        When:
        - 두 번째 요청 실행 (재시도 로직 포함)

        Then:
        - 1차 시도: stock_version=0 조건으로 UPDATE 실패 (이미 1로 변경됨)
        - 2차 시도: 재읽음 후, stock_version=1 조건으로 다시 시도
        - 재고 부족 에러: remaining_quantity=5 (20-15) < 필요 15개
        - InsufficientInventoryError 발생
        """
        from src.persistence.repositories.inventory_repository import InventoryRepository

        # Given: 첫 번째 요청이 15개를 차감 (시뮬레이션)
        test_db.query(PartnerAllocatedInventory).filter(
            PartnerAllocatedInventory.id == sample_inventory.id
        ).update({
            PartnerAllocatedInventory.remaining_quantity: 5,  # 20 - 15
            PartnerAllocatedInventory.stock_version: 1,
        })
        test_db.commit()

        # When: 두 번째 요청이 15개를 차감 시도
        # Then: 재고 부족 에러
        with pytest.raises(OrderException) as exc_info:
            InventoryRepository.decrease_inventory_with_optimistic_lock(
                test_db,
                inventory_id=sample_inventory.id,
                quantity=15,
                max_retries=3,
            )

        # stock_version=1로 재읽음 후 5개만 남았으므로 부족
        assert exc_info.value.code == "INSUFFICIENT_STOCK"

        # 최종 상태: 변경 없음
        test_db.refresh(sample_inventory)
        assert sample_inventory.remaining_quantity == 5
        assert sample_inventory.stock_version == 1
