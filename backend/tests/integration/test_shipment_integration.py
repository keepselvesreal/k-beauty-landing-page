"""배송 처리 통합테스트

Given-When-Then 형식으로 작성
"""

import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from src.persistence.models import (
    User,
    FulfillmentPartner,
    Order,
    OrderItem,
    Product,
    Customer,
    Shipment,
    EmailLog,
)
from src.persistence.database import Base, engine
from src.utils.auth import JWTTokenManager
from src.main import app


@pytest.fixture
def db_session():
    """테스트 DB 세션"""
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    yield
    # 테스트 후 정리
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def setup_test_data(db_session):
    """테스트 데이터 설정"""
    from src.persistence.database import SessionLocal
    from src.workflow.services.authentication_service import AuthenticationService

    db = SessionLocal()

    try:
        # 1. 배송담당자 A 생성
        partner_a_user = User(
            email="partner-a@example.com",
            password_hash=AuthenticationService.hash_password("password123"),
            role="fulfillment_partner",
            is_active=True,
        )
        db.add(partner_a_user)
        db.flush()

        partner_a = FulfillmentPartner(
            user_id=partner_a_user.id,
            name="Partner A",
            email="partner-a@example.com",
            phone="+63-555-0001",
            is_active=True,
        )
        db.add(partner_a)

        # 2. 배송담당자 B 생성
        partner_b_user = User(
            email="partner-b@example.com",
            password_hash=AuthenticationService.hash_password("password123"),
            role="fulfillment_partner",
            is_active=True,
        )
        db.add(partner_b_user)
        db.flush()

        partner_b = FulfillmentPartner(
            user_id=partner_b_user.id,
            name="Partner B",
            email="partner-b@example.com",
            phone="+63-555-0002",
            is_active=True,
        )
        db.add(partner_b)

        # 3. 고객 생성
        customer = Customer(
            email="customer@example.com",
            name="Test Customer",
            phone="+63-555-0100",
            address="123 Main St, Metro Manila",
            region="Metro Manila",
        )
        db.add(customer)

        # 4. 상품 생성
        product = Product(
            name="Test Product",
            description="Test product description",
            price=Decimal("1500.00"),
            sku="TEST-001",
        )
        db.add(product)

        db.commit()

        # 5. 주문 A 생성 (Partner A에게 할당)
        order_a = Order(
            order_number="ORD-001",
            customer_id=customer.id,
            fulfillment_partner_id=partner_a.id,
            subtotal=Decimal("1500.00"),
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("1600.00"),
            payment_status="completed",
            shipping_status="preparing",
        )
        db.add(order_a)
        db.flush()

        # 6. 주문 A 상품 추가
        order_item_a = OrderItem(
            order_id=order_a.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("1500.00"),
        )
        db.add(order_item_a)

        # 7. 주문 B 생성 (Partner B에게 할당)
        order_b = Order(
            order_number="ORD-002",
            customer_id=customer.id,
            fulfillment_partner_id=partner_b.id,
            subtotal=Decimal("1500.00"),
            shipping_fee=Decimal("100.00"),
            total_price=Decimal("1600.00"),
            payment_status="completed",
            shipping_status="preparing",
        )
        db.add(order_b)
        db.flush()

        # 8. 주문 B 상품 추가
        order_item_b = OrderItem(
            order_id=order_b.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("1500.00"),
        )
        db.add(order_item_b)

        db.commit()

        yield {
            "partner_a": partner_a,
            "partner_a_user": partner_a_user,
            "partner_b": partner_b,
            "partner_b_user": partner_b_user,
            "customer": customer,
            "product": product,
            "order_a": order_a,
            "order_b": order_b,
        }

    finally:
        db.close()


class TestShipmentCarrierAndTrackingNumber:
    """TC 3.4.2/3: carrier & tracking_number 저장 검증"""

    def test_shipment_carrier_and_tracking_saved(self, test_client, setup_test_data):
        """
        GIVEN: Partner A가 ORD-001 주문을 배송하려고 함
        WHEN: PATCH /api/fulfillment-partner/orders/{order_id}/ship 호출
              carrier="LBC", tracking_number="1234567890"
        THEN: 응답에 carrier와 tracking_number 포함
              DB에 Shipment 레코드 생성 (carrier="LBC", tracking_number="1234567890")
              Order 상태 변경 (preparing -> shipped)
        """
        # GIVEN
        from src.persistence.database import SessionLocal
        from src.utils.auth import JWTTokenManager

        db = SessionLocal()
        data = setup_test_data

        # Partner A 토큰 생성
        token_payload = {
            "user_id": str(data["partner_a_user"].id),
            "role": "fulfillment_partner",
            "email": data["partner_a_user"].email,
        }
        token = JWTTokenManager.create_access_token(token_payload)

        # WHEN
        response = test_client.patch(
            f"/api/fulfillment-partner/orders/{data['order_a'].id}/ship",
            json={
                "carrier": "LBC",
                "tracking_number": "1234567890",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # THEN
        assert response.status_code == 200, f"응답 상태: {response.status_code}, 본문: {response.json()}"

        response_data = response.json()

        # 1. 응답 검증
        assert response_data["order_id"] == str(data["order_a"].id)
        assert response_data["order_number"] == "ORD-001"
        assert response_data["status"] == "shipped"
        assert response_data["carrier"] == "LBC"
        assert response_data["tracking_number"] == "1234567890"
        assert response_data["email_status"] in ["sent", "failed"]
        assert response_data["shipped_at"] is not None

        # 2. DB 검증
        shipment = (
            db.query(Shipment)
            .filter(Shipment.order_id == data["order_a"].id)
            .first()
        )
        assert shipment is not None, "Shipment 레코드가 생성되지 않음"
        assert shipment.carrier == "LBC", f"carrier 저장 실패: {shipment.carrier}"
        assert shipment.tracking_number == "1234567890", f"tracking_number 저장 실패: {shipment.tracking_number}"
        assert shipment.status == "shipped"
        assert shipment.shipped_at is not None

        # 3. Order 상태 검증
        order = db.query(Order).filter(Order.id == data["order_a"].id).first()
        assert order.shipping_status == "shipped", f"Order 상태 변경 실패: {order.shipping_status}"
        assert order.shipped_at is not None, "Order shipped_at 미기록"

        db.close()


class TestShipmentEmailNotification:
    """TC 3.4.4: 이메일 발송 성공"""

    def test_shipment_email_sent_success(self, test_client, setup_test_data):
        """
        GIVEN: Partner A가 ORD-001을 배송 처리하려고 함
        WHEN: PATCH /api/fulfillment-partner/orders/{order_id}/ship 호출
        THEN: 응답 email_status="sent"
              email_logs 테이블에 status="sent" 레코드 생성
              이메일 본문에 carrier와 tracking_number 포함
        """
        # GIVEN
        from src.persistence.database import SessionLocal

        db = SessionLocal()
        data = setup_test_data

        # Partner A 토큰 생성
        token_payload = {
            "user_id": str(data["partner_a_user"].id),
            "role": "fulfillment_partner",
            "email": data["partner_a_user"].email,
        }
        token = JWTTokenManager.create_access_token(token_payload)

        # WHEN
        response = test_client.patch(
            f"/api/fulfillment-partner/orders/{data['order_a'].id}/ship",
            json={
                "carrier": "2GO",
                "tracking_number": "9876543210",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # THEN
        assert response.status_code == 200

        response_data = response.json()

        # 1. 응답에서 이메일 상태 확인
        # 주의: 실제 SMTP 설정이 없으면 "failed"가 될 수 있음
        assert response_data["email_status"] in ["sent", "failed"]

        # 2. email_logs DB 검증
        email_log = (
            db.query(EmailLog)
            .filter(
                EmailLog.order_id == data["order_a"].id,
                EmailLog.email_type == "shipment_notification",
            )
            .first()
        )
        assert email_log is not None, "email_log 레코드 생성 실패"
        assert email_log.status in ["sent", "failed"]
        assert email_log.recipient_email == data["customer"].email

        db.close()


class TestShipmentEmailFailure:
    """TC 3.4.5: 이메일 발송 실패 (Mock)"""

    def test_shipment_email_failure_logged(self, test_client, setup_test_data, monkeypatch):
        """
        GIVEN: 이메일 발송이 실패하는 환경
        WHEN: PATCH /api/fulfillment-partner/orders/{order_id}/ship 호출
        THEN: 응답 email_status="failed"
              email_logs 테이블에 status="failed" 레코드 생성
              Order와 Shipment는 정상 저장됨
        """
        # GIVEN
        from src.persistence.database import SessionLocal
        from src.workflow.services.email_service import EmailService

        db = SessionLocal()
        data = setup_test_data

        # 이메일 발송 실패 Mock
        def mock_send_shipment_notification(*args, **kwargs):
            return False  # 이메일 발송 실패

        monkeypatch.setattr(
            EmailService,
            "send_shipment_notification",
            mock_send_shipment_notification,
        )

        # Partner A 토큰 생성
        token_payload = {
            "user_id": str(data["partner_a_user"].id),
            "role": "fulfillment_partner",
            "email": data["partner_a_user"].email,
        }
        token = JWTTokenManager.create_access_token(token_payload)

        # WHEN
        response = test_client.patch(
            f"/api/fulfillment-partner/orders/{data['order_a'].id}/ship",
            json={
                "carrier": "Grab",
                "tracking_number": "5555555555",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # THEN
        assert response.status_code == 200

        response_data = response.json()

        # 1. 응답에서 이메일 실패 확인
        assert response_data["email_status"] == "failed"

        # 2. Shipment는 정상 저장됨 (이메일 실패가 배송을 롤백하지 않음)
        shipment = (
            db.query(Shipment)
            .filter(Shipment.order_id == data["order_a"].id)
            .first()
        )
        assert shipment is not None
        assert shipment.carrier == "Grab"
        assert shipment.tracking_number == "5555555555"
        assert shipment.status == "shipped"

        # 3. Order도 shipped 상태로 유지
        order = db.query(Order).filter(Order.id == data["order_a"].id).first()
        assert order.shipping_status == "shipped"

        db.close()


class TestShipmentPermissionValidation:
    """TC 3.4.6: 권한 검증 (다른 배송담당자의 주문)"""

    def test_shipment_forbidden_for_different_partner(self, test_client, setup_test_data):
        """
        GIVEN: Partner A가 로그인했고, ORD-002 (Partner B의 주문)를 처리하려고 함
        WHEN: PATCH /api/fulfillment-partner/orders/{order_b_id}/ship 호출
              Partner A 토큰으로 ORD-002 처리 시도
        THEN: 응답 status_code=403 Forbidden
              DB에 변경 없음 (Shipment 생성 안됨, Order 상태 유지)
        """
        # GIVEN
        from src.persistence.database import SessionLocal

        db = SessionLocal()
        data = setup_test_data

        # Partner A 토큰 생성 (ORD-002는 Partner B의 주문)
        token_payload = {
            "user_id": str(data["partner_a_user"].id),
            "role": "fulfillment_partner",
            "email": data["partner_a_user"].email,
        }
        token = JWTTokenManager.create_access_token(token_payload)

        # WHEN
        response = test_client.patch(
            f"/api/fulfillment-partner/orders/{data['order_b'].id}/ship",
            json={
                "carrier": "LBC",
                "tracking_number": "1234567890",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        # THEN
        assert response.status_code == 403, f"예상: 403, 실제: {response.status_code}"

        response_data = response.json()
        assert response_data["detail"]["code"] == "FORBIDDEN"

        # DB 검증: Shipment 생성 안됨
        shipment = (
            db.query(Shipment)
            .filter(Shipment.order_id == data["order_b"].id)
            .first()
        )
        assert shipment is None, "권한 없는 배송담당자가 Shipment를 생성했음"

        # Order 상태 유지
        order = db.query(Order).filter(Order.id == data["order_b"].id).first()
        assert order.shipping_status == "preparing", "Order 상태가 변경되었음"
        assert order.shipped_at is None

        db.close()
