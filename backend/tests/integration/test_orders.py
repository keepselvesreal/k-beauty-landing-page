"""주문 API Integration 테스트"""

import pytest
from fastapi.testclient import TestClient


class TestCreateOrder:
    """주문 생성 테스트"""

    def test_create_order_success(self, client: TestClient, complete_test_data):
        """주문 생성 성공"""
        data = complete_test_data

        response = client.post(
            "/api/orders",
            json={
                "customer_id": str(data["customer"].id),
                "product_id": str(data["product"].id),
                "quantity": 5,
                "region": "NCR",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["order_number"].startswith("ORD-")
        assert result["customer_id"] == str(data["customer"].id)
        assert result["subtotal"] == "250.00"  # 50 * 5
        assert result["shipping_fee"] == "100.00"  # NCR 배송료
        assert result["total_price"] == "350.00"  # 250 + 100
        assert result["payment_status"] == "pending"
        assert result["shipping_status"] == "preparing"

    def test_create_order_customer_not_found(self, client: TestClient, complete_test_data):
        """고객을 찾을 수 없을 때"""
        from uuid import uuid4

        response = client.post(
            "/api/orders",
            json={
                "customer_id": str(uuid4()),
                "product_id": str(complete_test_data["product"].id),
                "quantity": 5,
                "region": "NCR",
            },
        )

        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["code"] == "CUSTOMER_NOT_FOUND"

    def test_create_order_product_not_found(self, client: TestClient, complete_test_data):
        """상품을 찾을 수 없을 때"""
        from uuid import uuid4

        response = client.post(
            "/api/orders",
            json={
                "customer_id": str(complete_test_data["customer"].id),
                "product_id": str(uuid4()),
                "quantity": 5,
                "region": "NCR",
            },
        )

        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["code"] == "PRODUCT_NOT_FOUND"

    def test_create_order_insufficient_stock(self, client: TestClient, complete_test_data):
        """재고 부족"""
        data = complete_test_data

        response = client.post(
            "/api/orders",
            json={
                "customer_id": str(data["customer"].id),
                "product_id": str(data["product"].id),
                "quantity": 999,  # 초과
                "region": "NCR",
            },
        )

        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["code"] == "INSUFFICIENT_STOCK"

    def test_create_order_invalid_region(self, client: TestClient, complete_test_data):
        """유효하지 않은 지역"""
        data = complete_test_data

        response = client.post(
            "/api/orders",
            json={
                "customer_id": str(data["customer"].id),
                "product_id": str(data["product"].id),
                "quantity": 5,
                "region": "INVALID_REGION",
            },
        )

        assert response.status_code == 400
        result = response.json()
        assert result["detail"]["code"] == "INVALID_REGION"

    def test_create_order_different_regions(self, client: TestClient, complete_test_data):
        """지역별 배송료 확인"""
        data = complete_test_data

        regions_and_fees = [
            ("NCR", "100.00"),
            ("Luzon", "120.00"),
            ("Visayas", "140.00"),
            ("Mindanao", "160.00"),
        ]

        for region, expected_fee in regions_and_fees:
            response = client.post(
                "/api/orders",
                json={
                    "customer_id": str(data["customer"].id),
                    "product_id": str(data["product"].id),
                    "quantity": 1,
                    "region": region,
                },
            )

            assert response.status_code == 200
            result = response.json()
            assert result["shipping_fee"] == expected_fee


class TestGetOrder:
    """주문 조회 테스트"""

    def test_get_order_success(self, client: TestClient, complete_test_data):
        """주문 조회 성공"""
        data = complete_test_data

        # 먼저 주문 생성
        create_response = client.post(
            "/api/orders",
            json={
                "customer_id": str(data["customer"].id),
                "product_id": str(data["product"].id),
                "quantity": 5,
                "region": "NCR",
            },
        )

        assert create_response.status_code == 200
        order_number = create_response.json()["order_number"]

        # 주문 조회
        get_response = client.get(f"/api/orders/{order_number}")

        assert get_response.status_code == 200
        result = get_response.json()
        assert result["order_number"] == order_number
        assert result["payment_status"] == "pending"
        assert result["shipping_status"] == "preparing"

    def test_get_order_not_found(self, client: TestClient):
        """주문을 찾을 수 없을 때"""
        response = client.get("/api/orders/ORD-20251128-INVALID")

        assert response.status_code == 404
        result = response.json()
        assert result["detail"]["code"] == "ORDER_NOT_FOUND"
