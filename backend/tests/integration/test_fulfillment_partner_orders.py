"""배송담당자 주문 조회 API Integration 테스트"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.persistence.models import User, FulfillmentPartner, PartnerAllocatedInventory
from src.utils.auth import JWTTokenManager
from src.workflow.services.order_service import OrderService
from src.workflow.services.fulfillment_service import FulfillmentService
from src.persistence.repositories.order_repository import OrderRepository


class TestFulfillmentPartnerOrders:
    """배송담당자 주문 목록 조회 테스트 (기능 2)"""

    # ==================== Given: 테스트 데이터 Setup ====================

    @pytest.fixture
    def partner_with_user(self, test_db: Session):
        """Given: 배송담당자 및 사용자 설정"""
        # User 생성
        user = User(
            email="partner.test@example.com",
            password_hash="hashed_password",
            role="fulfillment_partner",
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # FulfillmentPartner 생성
        partner = FulfillmentPartner(
            user_id=user.id,
            name="NCR Fulfillment Hub",
            email="partner.test@example.com",
            phone="09123456789",
            address="NCR Warehouse",
            region="NCR",
            is_active=True,
        )
        test_db.add(partner)
        test_db.commit()
        test_db.refresh(partner)

        return {"user": user, "partner": partner}

    @pytest.fixture
    def partner_orders_preparing_and_shipped(
        self,
        complete_test_data,
        partner_with_user,
        test_db: Session,
    ):
        """Given: 배송담당자에게 할당된 주문 생성 (preparing 2개 + shipped 1개, 총 재고 20개)"""
        from src.persistence.models import Order, OrderItem
        from decimal import Decimal
        from uuid import uuid4
        from datetime import datetime

        partner = partner_with_user["partner"]

        # 배송담당자에 재고 할당 (상품 총 20개)
        inventory = PartnerAllocatedInventory(
            partner_id=partner.id,
            product_id=complete_test_data["product"].id,
            allocated_quantity=20,
            remaining_quantity=5,  # 할당 후 5개 남음 (5+10+5=20)
            stock_version=0,
        )
        test_db.add(inventory)
        test_db.commit()

        # 주문 1: 5개 (payment_status=completed, shipping_status=preparing)
        order1 = Order(
            order_number=f"ORD-{uuid4()}",
            customer_id=complete_test_data["customer"].id,
            fulfillment_partner_id=partner.id,
            subtotal=Decimal("250.00"),  # 50 * 5
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("350.00"),
            payment_status="completed",
            shipping_status="preparing",
        )
        test_db.add(order1)
        test_db.commit()
        test_db.refresh(order1)

        order_item1 = OrderItem(
            order_id=order1.id,
            product_id=complete_test_data["product"].id,
            quantity=5,
            unit_price=Decimal("50.00"),
        )
        test_db.add(order_item1)
        test_db.commit()

        # 주문 2: 10개 (payment_status=completed, shipping_status=preparing)
        order2 = Order(
            order_number=f"ORD-{uuid4()}",
            customer_id=complete_test_data["customer"].id,
            fulfillment_partner_id=partner.id,
            subtotal=Decimal("500.00"),  # 50 * 10
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("600.00"),
            payment_status="completed",
            shipping_status="preparing",
        )
        test_db.add(order2)
        test_db.commit()
        test_db.refresh(order2)

        order_item2 = OrderItem(
            order_id=order2.id,
            product_id=complete_test_data["product"].id,
            quantity=10,
            unit_price=Decimal("50.00"),
        )
        test_db.add(order_item2)
        test_db.commit()

        # 주문 3: 5개 (payment_status=completed, shipping_status=shipped - 배제)
        order3 = Order(
            order_number=f"ORD-{uuid4()}",
            customer_id=complete_test_data["customer"].id,
            fulfillment_partner_id=partner.id,
            subtotal=Decimal("250.00"),  # 50 * 5
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("350.00"),
            payment_status="completed",
            shipping_status="shipped",
        )
        test_db.add(order3)
        test_db.commit()
        test_db.refresh(order3)

        order_item3 = OrderItem(
            order_id=order3.id,
            product_id=complete_test_data["product"].id,
            quantity=5,
            unit_price=Decimal("50.00"),
        )
        test_db.add(order_item3)
        test_db.commit()

        return {
            "partner": partner,
            "user": partner_with_user["user"],
            "orders": {
                "preparing_1": order1,
                "preparing_2": order2,
                "shipped": order3,
            },
        }

    def _create_jwt_token(self, user):
        """Helper: JWT 토큰 생성"""
        token_payload = {
            "user_id": str(user.id),
            "role": user.role,
            "email": user.email,
        }
        return JWTTokenManager.create_access_token(token_payload)

    # ==================== TC 3.2.1: API 호출 성공 ====================

    def test_tc_3_2_1_get_fulfillment_partner_orders_success(
        self,
        client: TestClient,
        partner_orders_preparing_and_shipped,
    ):
        """
        TC 3.2.1: /api/fulfillment-partner/orders 호출 성공

        Given:
        - 배송담당자(NCR Fulfillment Hub)가 존재
        - 배송담당자에게 할당된 주문 2개:
          * 주문 1: 5개, payment_status=completed, shipping_status=preparing
          * 주문 2: 10개, payment_status=completed, shipping_status=preparing
        - 배제될 주문 1개:
          * 주문 3: 5개, payment_status=completed, shipping_status=shipped

        When:
        - JWT 토큰을 포함하여 GET /api/fulfillment-partner/orders 호출

        Then:
        - HTTP 200 응답
        - 응답에 partner_id, partner_name, orders 포함
        - 결제 완료 + preparing 상태의 주문 2개만 조회
        - shipped 상태 주문은 제외됨
        """
        # When
        access_token = self._create_jwt_token(partner_orders_preparing_and_shipped["user"])
        response = client.get(
            "/api/fulfillment-partner/orders",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Then
        assert response.status_code == 200
        result = response.json()

        # 배송담당자 정보 검증
        assert result["partner_id"] == str(partner_orders_preparing_and_shipped["partner"].id)
        assert result["partner_name"] == "NCR Fulfillment Hub"
        assert "orders" in result

        # 결제 완료 + preparing 상태 주문 2개만 조회
        assert len(result["orders"]) == 2

        # 각 주문의 필수 필드 검증
        for order_data in result["orders"]:
            assert "order_id" in order_data
            assert "order_number" in order_data
            assert order_data["order_number"].startswith("ORD-")
            assert "customer_email" in order_data
            assert "products" in order_data
            assert isinstance(order_data["products"], list)
            assert len(order_data["products"]) > 0
            assert "shipping_address" in order_data
            assert "total_price" in order_data
            assert order_data["status"] == "preparing"
            assert "created_at" in order_data

    # ==================== TC 3.2.4: 상태 필터링 ====================

    def test_tc_3_2_4_only_completed_and_preparing_orders(
        self,
        client: TestClient,
        partner_orders_preparing_and_shipped,
    ):
        """
        TC 3.2.4: payment_status=completed AND shipping_status=preparing 주문만 조회

        Given:
        - 배송담당자에게 할당된 주문 3개:
          * 주문 1: payment_status=completed, shipping_status=preparing ✓
          * 주문 2: payment_status=completed, shipping_status=preparing ✓
          * 주문 3: payment_status=completed, shipping_status=shipped ✗

        When:
        - JWT 토큰을 포함하여 GET /api/fulfillment-partner/orders 호출

        Then:
        - HTTP 200 응답
        - 주문 1, 2만 반환 (결제 완료 + preparing 상태)
        - 주문 3은 제외 (shipped 상태)
        """
        # When
        access_token = self._create_jwt_token(partner_orders_preparing_and_shipped["user"])
        response = client.get(
            "/api/fulfillment-partner/orders",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Then
        assert response.status_code == 200
        result = response.json()

        # 조건을 만족하는 주문은 2개
        assert len(result["orders"]) == 2

        # 모든 반환된 주문이 preparing 상태임을 검증
        for order_data in result["orders"]:
            assert order_data["status"] == "preparing"

        # shipped 상태 주문의 order_id는 포함되지 않음
        shipped_order_id = str(partner_orders_preparing_and_shipped["orders"]["shipped"].id)
        returned_order_ids = [
            order_data["order_id"] for order_data in result["orders"]
        ]
        assert shipped_order_id not in returned_order_ids

    # ==================== 엣지 케이스 ====================

    def test_empty_orders_when_no_allocation(
        self,
        client: TestClient,
        partner_with_user,
    ):
        """
        Given: 배송담당자가 존재하지만 할당된 주문이 없음

        When: GET /api/fulfillment-partner/orders 호출

        Then: HTTP 200, 빈 orders 리스트 반환
        """
        # When
        access_token = self._create_jwt_token(partner_with_user["user"])
        response = client.get(
            "/api/fulfillment-partner/orders",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Then
        assert response.status_code == 200
        result = response.json()
        assert result["partner_id"] == str(partner_with_user["partner"].id)
        assert len(result["orders"]) == 0

    def test_unauthorized_without_token(
        self,
        client: TestClient,
    ):
        """
        Given: JWT 토큰 없음

        When: GET /api/fulfillment-partner/orders 호출

        Then: HTTP 401 Unauthorized 반환
        """
        # When
        response = client.get("/api/fulfillment-partner/orders")

        # Then
        assert response.status_code == 401

    def test_unauthorized_with_invalid_token(
        self,
        client: TestClient,
    ):
        """
        Given: 유효하지 않은 JWT 토큰

        When: GET /api/fulfillment-partner/orders 호출

        Then: HTTP 401 Unauthorized 반환
        """
        # When
        response = client.get(
            "/api/fulfillment-partner/orders",
            headers={"Authorization": "Bearer invalid_token_xyz"},
        )

        # Then
        assert response.status_code == 401
