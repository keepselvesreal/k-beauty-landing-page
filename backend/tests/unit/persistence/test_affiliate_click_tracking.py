"""Affiliate 클릭 추적 테스트"""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from src.persistence.models import Affiliate, AffiliateClick
from src.persistence.repositories.affiliate_repository import AffiliateRepository


class TestAffiliateClickTracking:
    """클릭 수 추적"""

    def test_valid_affiliate_click_is_recorded(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
    ):
        """TC-B.1.1: 유효한 어필리에이트 코드의 클릭이 정상 기록된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        # When
        click = AffiliateClick(affiliate_id=affiliate_active.id)
        test_db.add(click)
        test_db.commit()
        test_db.refresh(affiliate_active)

        # Then
        assert len(affiliate_active.clicks) == 1
        recorded_click = affiliate_active.clicks[0]
        assert recorded_click.affiliate_id == affiliate_active.id
        assert recorded_click.clicked_at is not None

    def test_multiple_clicks_are_all_recorded(
        self,
        test_db: Session,
        affiliate_active: Affiliate,
    ):
        """TC-B.1.2: 여러 사용자로부터 클릭이 오면 모두 기록된다"""
        # Given
        test_db.add(affiliate_active)
        test_db.commit()

        # When - 5번 클릭
        for _ in range(5):
            click = AffiliateClick(affiliate_id=affiliate_active.id)
            test_db.add(click)
        test_db.commit()
        test_db.refresh(affiliate_active)

        # Then
        assert len(affiliate_active.clicks) == 5

    def test_invalid_affiliate_code_click_fails(
        self,
        test_db: Session,
    ):
        """TC-B.1.3: 존재하지 않는 코드로 클릭하면 기록되지 않는다"""
        # Given
        from uuid import uuid4

        non_existent_affiliate_id = uuid4()

        # When/Then
        # 존재하지 않는 ID로 클릭 시도
        with pytest.raises(Exception):  # ForeignKey constraint 위반
            click = AffiliateClick(affiliate_id=non_existent_affiliate_id)
            test_db.add(click)
            test_db.commit()

        # 트랜잭션 롤백
        test_db.rollback()

        # 클릭 기록이 없어야 함
        all_clicks = test_db.query(AffiliateClick).all()
        assert len(all_clicks) == 0

    def test_inactive_affiliate_click_is_recorded_but_marked_inactive(
        self,
        test_db: Session,
        affiliate_inactive: Affiliate,
    ):
        """TC-B.1.4: 비활성화된 어필리에이트 코드로도 클릭은 기록되지만, 비활성 상태임"""
        # Given
        test_db.add(affiliate_inactive)
        test_db.commit()

        # When
        click = AffiliateClick(affiliate_id=affiliate_inactive.id)
        test_db.add(click)
        test_db.commit()
        test_db.refresh(affiliate_inactive)

        # Then
        # 클릭은 기록됨
        assert len(affiliate_inactive.clicks) == 1
        # 하지만 어필리에이트가 비활성 상태
        assert affiliate_inactive.is_active is False
