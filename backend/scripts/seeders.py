"""각 모델별 Seeder 클래스들"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import Dict, List, Any

from sqlalchemy.orm import Session

from src.persistence.models import (
    User,
    Product,
    FulfillmentPartner,
    PartnerAllocatedInventory,
    ShippingRate,
    Customer,
    Order,
    OrderItem,
    Affiliate,
    AffiliateClick,
    AffiliateSale,
    AffiliatePayment,
    Shipment,
)
from src.workflow.services.authentication_service import AuthenticationService


class BaseSeeder(ABC):
    """Seeder 기본 클래스"""

    def __init__(self, db: Session):
        self.db = db

    @abstractmethod
    def seed(self) -> Dict[str, Any]:
        """데이터 생성 및 반환"""
        pass

    def commit(self):
        """커밋"""
        self.db.commit()

    def flush(self):
        """플러시"""
        self.db.flush()


class ProductSeeder(BaseSeeder):
    """상품 Seeder"""

    def seed(self, products_data: List[Dict] = None) -> Dict[str, Any]:
        """상품 생성"""
        if products_data is None:
            products_data = [
                {
                    "name": "조선미녀 맑은쌀 선크림 50ml",
                    "description": "프리미엄 쌀 추출물 함유 자외선 차단 크림, 민감한 피부에 안전",
                    "price": 28.99,
                    "sku": "JOSEONMINYEO-RICECREAM-50ML",
                    "image_url": "https://example.com/joseon-rice-cream.jpg",
                },
            ]

        created_products = {}
        for product_data in products_data:
            product = Product(
                id=uuid4(),
                name=product_data["name"],
                description=product_data["description"],
                price=Decimal(str(product_data["price"])),
                sku=product_data["sku"],
                image_url=product_data.get("image_url", ""),
                is_active=product_data.get("is_active", True),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(product)
            created_products[product_data["sku"]] = product

        self.commit()

        return {
            "type": "products",
            "count": len(created_products),
            "data": created_products,
        }


class UserSeeder(BaseSeeder):
    """사용자 (배송담당자) Seeder"""

    def seed(self, partners_data: List[Dict] = None) -> Dict[str, Any]:
        """배송담당자 사용자 생성"""
        if partners_data is None:
            partners_data = [
                {
                    "name": "조선미녀 필리핀 배송담당자",
                    "email": "ncr.partner@example.com",
                    "phone": "+63-917-123-4567",
                    "address": "Manila Business District, Metro Manila",
                    "region": "NCR",
                },
            ]

        created_users = {}
        partner_credentials = {}

        for partner_data in partners_data:
            email = partner_data["email"]
            password = f"Partner@{partner_data['region']}123"
            password_hash = AuthenticationService.hash_password(password)

            user = User(
                id=uuid4(),
                email=email,
                password_hash=password_hash,
                role="fulfillment_partner",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(user)
            self.flush()

            created_users[partner_data["name"]] = {
                "user": user,
                "partner_data": partner_data,
            }
            partner_credentials[partner_data["name"]] = {
                "email": email,
                "password": password,
                "user_id": str(user.id),
            }

        self.commit()

        return {
            "type": "users",
            "count": len(created_users),
            "data": created_users,
            "credentials": partner_credentials,
        }


class FulfillmentPartnerSeeder(BaseSeeder):
    """배송담당자 Seeder"""

    def seed(self, users_result: Dict = None) -> Dict[str, Any]:
        """배송담당자 생성 (User 생성 이후)"""
        if users_result is None or "data" not in users_result:
            raise ValueError(
                "FulfillmentPartner 생성을 위해 먼저 User를 생성해야 합니다."
            )

        created_partners = {}
        user_data_dict = users_result["data"]

        for partner_name, user_info in user_data_dict.items():
            user = user_info["user"]
            partner_data = user_info["partner_data"]

            partner = FulfillmentPartner(
                id=uuid4(),
                user_id=user.id,
                name=partner_data["name"],
                email=partner_data["email"],
                phone=partner_data["phone"],
                address=partner_data["address"],
                region=partner_data["region"],
                is_active=partner_data.get("is_active", True),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(partner)
            created_partners[partner_name] = partner

        self.commit()

        return {
            "type": "fulfillment_partners",
            "count": len(created_partners),
            "data": created_partners,
        }


class ShippingRateSeeder(BaseSeeder):
    """배송료 Seeder"""

    def seed(self, rates_data: List[Dict] = None) -> Dict[str, Any]:
        """배송료 생성"""
        if rates_data is None:
            rates_data = [
                {"region": "NCR", "fee": 100},
                {"region": "Luzon", "fee": 120},
                {"region": "Visayas", "fee": 140},
                {"region": "Mindanao", "fee": 160},
            ]

        created_rates = {}
        for rate_data in rates_data:
            rate = ShippingRate(
                id=uuid4(),
                region=rate_data["region"],
                fee=Decimal(str(rate_data["fee"])),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(rate)
            created_rates[rate_data["region"]] = rate

        self.commit()

        return {
            "type": "shipping_rates",
            "count": len(created_rates),
            "data": created_rates,
        }


class CustomerSeeder(BaseSeeder):
    """고객 Seeder"""

    def seed(self, customers_data: List[Dict] = None) -> Dict[str, Any]:
        """고객 생성"""
        if customers_data is None:
            customers_data = [
                {
                    "email": "maria.santos@example.ph",
                    "name": "Maria Santos",
                    "phone": "09178901234",
                    "address": "Makati Commercial Center, Makati City",
                    "region": "NCR",
                },
                {
                    "email": "juan.dela.cruz@example.ph",
                    "name": "Juan Dela Cruz",
                    "phone": "09267890123",
                    "address": "Cebu IT Park, Cebu City",
                    "region": "Visayas",
                },
                {
                    "email": "rosa.garcia@example.ph",
                    "name": "Rosa Garcia",
                    "phone": "09356789012",
                    "address": "SM City Davao, Davao City",
                    "region": "Mindanao",
                },
            ]

        created_customers = []
        for cust_data in customers_data:
            customer = Customer(
                id=uuid4(),
                email=cust_data["email"],
                name=cust_data["name"],
                phone=cust_data["phone"],
                address=cust_data["address"],
                region=cust_data["region"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(customer)
            created_customers.append(customer)

        self.commit()

        return {
            "type": "customers",
            "count": len(created_customers),
            "data": created_customers,
        }


class InventorySeeder(BaseSeeder):
    """재고 할당 Seeder"""

    def seed(
        self,
        partners_result: Dict = None,
        products_result: Dict = None,
        inventory_data: List[Dict] = None,
    ) -> Dict[str, Any]:
        """배송담당자별 재고 할당"""
        if (
            not partners_result
            or not products_result
            or "data" not in partners_result
            or "data" not in products_result
        ):
            raise ValueError("재고 할당을 위해 먼저 배송담당자와 상품을 생성해야 합니다.")

        if inventory_data is None:
            inventory_data = [
                {
                    "partner_name": "조선미녀 필리핀 배송담당자",
                    "product_sku": "JOSEONMINYEO-RICECREAM-50ML",
                    "quantity": 20,
                },
            ]

        partners_dict = partners_result["data"]
        products_dict = products_result["data"]

        created_inventory = []
        total_quantity = 0

        for inv_data in inventory_data:
            partner = partners_dict.get(inv_data["partner_name"])
            product = products_dict.get(inv_data["product_sku"])

            if partner and product:
                allocated_inv = PartnerAllocatedInventory(
                    id=uuid4(),
                    partner_id=partner.id,
                    product_id=product.id,
                    allocated_quantity=inv_data["quantity"],
                    remaining_quantity=inv_data["quantity"],
                    stock_version=0,
                    allocated_date=datetime.utcnow().date(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                self.db.add(allocated_inv)
                created_inventory.append(allocated_inv)
                total_quantity += inv_data["quantity"]

        self.commit()

        return {
            "type": "inventory",
            "count": len(created_inventory),
            "total_quantity": total_quantity,
            "data": created_inventory,
        }


class OrderSeeder(BaseSeeder):
    """주문 Seeder"""

    def seed(
        self,
        customers_result: Dict = None,
        partners_result: Dict = None,
        products_result: Dict = None,
        orders_data: List[Dict] = None,
    ) -> Dict[str, Any]:
        """주문 생성"""
        if (
            not customers_result
            or not partners_result
            or not products_result
            or "data" not in customers_result
            or "data" not in partners_result
            or "data" not in products_result
        ):
            raise ValueError("주문 생성을 위해 먼저 고객, 배송담당자, 상품을 생성해야 합니다.")

        if orders_data is None:
            orders_data = [
                {
                    "customer_index": 0,  # Maria Santos
                    "partner_name": "조선미녀 필리핀 배송담당자",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 2},
                    ],
                    "shipping_fee": Decimal("100"),
                },
                {
                    "customer_index": 1,  # Juan Dela Cruz
                    "partner_name": "조선미녀 필리핀 배송담당자",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 1},
                    ],
                    "shipping_fee": Decimal("100"),
                },
            ]

        customers_list = customers_result["data"]
        partners_dict = partners_result["data"]
        products_dict = products_result["data"]

        created_orders = []

        for order_data in orders_data:
            customer = customers_list[order_data["customer_index"]]
            partner = partners_dict.get(order_data["partner_name"])

            if not partner:
                continue

            # 총액 계산
            subtotal = Decimal("0")
            items = []

            for item_data in order_data["items"]:
                product = products_dict.get(item_data["product_sku"])
                if product:
                    quantity = item_data["quantity"]
                    subtotal += product.price * Decimal(str(quantity))
                    items.append({"product": product, "quantity": quantity})

            shipping_fee = order_data.get("shipping_fee", Decimal("0"))
            total_price = subtotal + shipping_fee

            order = Order(
                id=uuid4(),
                order_number=f"ORD-{uuid4().hex[:8].upper()}",
                customer_id=customer.id,
                fulfillment_partner_id=partner.id,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_price=total_price,
                payment_status="completed",
                shipping_status="preparing",
                paypal_order_id=f"PAYPAL-{uuid4().hex[:8].upper()}",
                paypal_capture_id=f"CAPTURE-{uuid4().hex[:8].upper()}",
                paypal_fee=subtotal * Decimal("0.034"),  # 3.4% 수수료
                profit=Decimal("80.00"),
                paid_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(order)
            self.flush()

            # OrderItem 생성
            for item_info in items:
                order_item = OrderItem(
                    id=uuid4(),
                    order_id=order.id,
                    product_id=item_info["product"].id,
                    quantity=item_info["quantity"],
                    unit_price=item_info["product"].price,
                    created_at=datetime.utcnow(),
                )
                self.db.add(order_item)

            created_orders.append(order)

        self.commit()

        return {
            "type": "orders",
            "count": len(created_orders),
            "data": created_orders,
        }


class AffiliateSeeder(BaseSeeder):
    """인플루언서 (어필리에이트) Seeder"""

    def seed(self, affiliate_data: Dict = None) -> Dict[str, Any]:
        """인플루언서 및 어필리에이트 데이터 생성"""
        if affiliate_data is None:
            affiliate_data = {
                "email": "influencer@example.com",
                "password": "test123456",
                "code": "santa-here-kim_influencer",
                "name": "Kim Taesoo (인플루언서)",
            }

        try:
            # 1. 사용자 생성
            password_hash = AuthenticationService.hash_password(affiliate_data["password"])
            user = User(
                id=uuid4(),
                email=affiliate_data["email"],
                password_hash=password_hash,
                role="influencer",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(user)
            self.flush()

            # 2. 어필리에이트 생성
            affiliate = Affiliate(
                id=uuid4(),
                user_id=user.id,
                code=affiliate_data["code"],
                name=affiliate_data["name"],
                email=affiliate_data["email"],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(affiliate)
            self.flush()

            # 3. 테스트 클릭 데이터 생성 (150개)
            for i in range(150):
                click = AffiliateClick(
                    id=uuid4(),
                    affiliate_id=affiliate.id,
                    clicked_at=datetime.utcnow() - timedelta(days=30 - (i // 5)),
                )
                self.db.add(click)

            # 4. 테스트 판매 데이터 생성 (5건)
            # Note: AffiliateSale의 order_id는 필수 외래키이므로 실제 orders가 필요함
            # 테스트 목적이므로 실제 판매 데이터는 대시보드에서 주문 생성 시 자동으로 추가됨
            # for i in range(5):
            #     sale = AffiliateSale(
            #         id=uuid4(),
            #         affiliate_id=affiliate.id,
            #         order_id=...,  # 실제 order ID 필요
            #         commission_amount=Decimal("16.00"),
            #         created_at=datetime.utcnow(),
            #     )
            #     self.db.add(sale)

            # 5. 테스트 지급 데이터 생성 (부분 지급: 30)
            payment = AffiliatePayment(
                id=uuid4(),
                affiliate_id=affiliate.id,
                amount=Decimal("30.00"),
                status="completed",
                payment_method="PayPal",
                paid_at=datetime.utcnow() - timedelta(days=15),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(payment)

            self.commit()

            return {
                "type": "influencer",
                "count": 1,
                "data": {
                    "user": user,
                    "affiliate": affiliate,
                },
                "credentials": {
                    "email": affiliate_data["email"],
                    "password": affiliate_data["password"],
                    "user_id": str(user.id),
                    "affiliate_code": affiliate_data["code"],
                },
            }
        except Exception as e:
            self.db.rollback()
            raise e


class RefundSeeder(BaseSeeder):
    """환불 요청 Seeder"""

    def seed(self, orders_result: Dict = None) -> Dict[str, Any]:
        """
        환불 요청 데이터 생성 (Order 생성 후)

        주어진 주문들을 배송 완료 상태로 만들고, 일부를 환불 요청 상태로 변경
        """
        if not orders_result or "data" not in orders_result:
            raise ValueError("환불 요청 생성을 위해 먼저 Order를 생성해야 합니다.")

        orders = orders_result["data"]
        created_refunds = []

        # 각 주문에 대해 배송 완료 상태로 만들기
        for idx, order in enumerate(orders):
            # 배송 완료 상태로 변경
            order.shipping_status = "delivered"
            order.payment_status = "completed"
            self.db.add(order)

            # 첫 번째 주문을 환불 요청 상태로 변경
            if idx == 0:
                order.refund_status = "refund_requested"
                order.refund_reason = "상품 불량"
                order.refund_requested_at = datetime.utcnow()
                created_refunds.append(order)

        self.commit()

        return {
            "type": "refunds",
            "count": len(created_refunds),
            "data": created_refunds,
        }
