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
    ShippingCommissionPayment,
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
                profit_per_unit=Decimal(str(product_data.get("profit_per_unit", 80))),
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
                    "name": "조선미녀 필리핀 배송담당자 - NCR",
                    "email": "ncr.partner@example.com",
                    "phone": "+63-917-123-4567",
                    "address": "Manila Business District, Metro Manila",
                    "region": "NCR",
                },
                {
                    "name": "조선미녀 필리핀 배송담당자 - Visayas",
                    "email": "visayas.partner@example.com",
                    "phone": "+63-917-234-5678",
                    "address": "Cebu IT Park, Cebu City",
                    "region": "Visayas",
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
                # 배송 준비 중 (preparing) - 배송담당자 1 (NCR)
                {
                    "customer_index": 0,  # Maria Santos
                    "partner_name": "조선미녀 필리핀 배송담당자 - NCR",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 2},
                    ],
                    "shipping_fee": Decimal("100"),
                    "shipping_status": "preparing",
                    "shipping_commission": Decimal("20"),
                },
                {
                    "customer_index": 1,  # Juan Dela Cruz
                    "partner_name": "조선미녀 필리핀 배송담당자 - NCR",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 1},
                    ],
                    "shipping_fee": Decimal("100"),
                    "shipping_status": "preparing",
                    "shipping_commission": Decimal("20"),
                },
                {
                    "customer_index": 2,  # Rosa Garcia
                    "partner_name": "조선미녀 필리핀 배송담당자 - NCR",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 3},
                    ],
                    "shipping_fee": Decimal("100"),
                    "shipping_status": "preparing",
                    "shipping_commission": Decimal("20"),
                },
                # 배송 중 (in_transit) - 배송담당자 1 (NCR)
                {
                    "customer_index": 0,  # Maria Santos
                    "partner_name": "조선미녀 필리핀 배송담당자 - NCR",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 1},
                    ],
                    "shipping_fee": Decimal("100"),
                    "shipping_status": "in_transit",
                    "shipping_commission": Decimal("20"),
                },
                {
                    "customer_index": 1,  # Juan Dela Cruz
                    "partner_name": "조선미녀 필리핀 배송담당자 - NCR",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 2},
                    ],
                    "shipping_fee": Decimal("100"),
                    "shipping_status": "in_transit",
                    "shipping_commission": Decimal("20"),
                },
                {
                    "customer_index": 2,  # Rosa Garcia
                    "partner_name": "조선미녀 필리핀 배송담당자 - NCR",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 1},
                    ],
                    "shipping_fee": Decimal("100"),
                    "shipping_status": "in_transit",
                    "shipping_commission": Decimal("20"),
                },
                # 배송 완료 (delivered) - 배송담당자 2 (Visayas)
                {
                    "customer_index": 0,  # Maria Santos
                    "partner_name": "조선미녀 필리핀 배송담당자 - Visayas",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 2},
                    ],
                    "shipping_fee": Decimal("120"),
                    "shipping_status": "delivered",
                    "shipping_commission": Decimal("25"),
                },
                {
                    "customer_index": 1,  # Juan Dela Cruz
                    "partner_name": "조선미녀 필리핀 배송담당자 - Visayas",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 3},
                    ],
                    "shipping_fee": Decimal("120"),
                    "shipping_status": "delivered",
                    "shipping_commission": Decimal("25"),
                },
                {
                    "customer_index": 2,  # Rosa Garcia
                    "partner_name": "조선미녀 필리핀 배송담당자 - Visayas",
                    "items": [
                        {"product_sku": "JOSEONMINYEO-RICECREAM-50ML", "quantity": 1},
                    ],
                    "shipping_fee": Decimal("120"),
                    "shipping_status": "delivered",
                    "shipping_commission": Decimal("25"),
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

            # 총액 및 순이윤 계산
            subtotal = Decimal("0")
            total_profit = Decimal("0")
            items = []

            for item_data in order_data["items"]:
                product = products_dict.get(item_data["product_sku"])
                if product:
                    quantity = item_data["quantity"]
                    subtotal += product.price * Decimal(str(quantity))

                    # 순이윤 계산: profit_per_unit * quantity
                    profit_per_unit = Decimal(str(product.profit_per_unit or 80))
                    total_profit += profit_per_unit * quantity

                    items.append({
                        "product": product,
                        "quantity": quantity,
                        "profit_per_unit": profit_per_unit,
                    })

            shipping_fee = order_data.get("shipping_fee", Decimal("0"))
            total_price = subtotal + shipping_fee
            shipping_status = order_data.get("shipping_status", "preparing")
            shipping_commission = order_data.get("shipping_commission", Decimal("0"))

            order = Order(
                id=uuid4(),
                order_number=f"ORD-{uuid4().hex[:8].upper()}",
                customer_id=customer.id,
                fulfillment_partner_id=partner.id,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total_price=total_price,
                payment_status="completed",
                shipping_status=shipping_status,
                paypal_order_id=f"PAYPAL-{uuid4().hex[:8].upper()}",
                paypal_capture_id=f"CAPTURE-{uuid4().hex[:8].upper()}",
                paypal_transaction_fee=subtotal * Decimal("0.034"),  # 3.4% 수수료
                total_profit=total_profit,
                shipping_commission=shipping_commission,
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
                    profit_per_item=item_info["profit_per_unit"],
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

    def seed(self, affiliates_data: List[Dict] = None, orders_result: Dict = None) -> Dict[str, Any]:
        """인플루언서 및 어필리에이트 데이터 생성"""
        if affiliates_data is None:
            affiliates_data = [
                {
                    "email": "influencer1@example.com",
                    "password": "test123456",
                    "code": "influencer-no-payment",
                    "name": "Influencer No Payment",
                    "has_pending_payment": False,
                },
                {
                    "email": "influencer2@example.com",
                    "password": "test123456",
                    "code": "influencer-with-payment",
                    "name": "Influencer With Payment",
                    "has_pending_payment": True,
                },
            ]

        try:
            created_affiliates = []
            credentials = []
            orders = orders_result["data"] if orders_result and "data" in orders_result else []

            for idx, affiliate_data in enumerate(affiliates_data):
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

                # 4. 지급 예정액이 있는 인플루언서의 경우 판매 데이터 생성
                if affiliate_data.get("has_pending_payment") and orders:
                    # 처음 3개 주문에 대해 판매 데이터 생성
                    for order_idx in range(min(3, len(orders))):
                        sale = AffiliateSale(
                            id=uuid4(),
                            affiliate_id=affiliate.id,
                            order_id=orders[order_idx].id,
                            marketing_commission=Decimal("15.00"),
                            created_at=datetime.utcnow(),
                        )
                        self.db.add(sale)

                    # 5. 미지급 상태의 지급 데이터 생성 (지급 예정액)
                    payment = AffiliatePayment(
                        id=uuid4(),
                        affiliate_id=affiliate.id,
                        amount=Decimal("45.00"),
                        status="pending",
                        payment_method="PayPal",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    self.db.add(payment)
                else:
                    # 지급 예정액이 없는 경우는 아무것도 하지 않음
                    pass

                created_affiliates.append(affiliate)
                credentials.append({
                    "email": affiliate_data["email"],
                    "password": affiliate_data["password"],
                    "user_id": str(user.id),
                    "affiliate_code": affiliate_data["code"],
                })

            self.commit()

            return {
                "type": "influencers",
                "count": len(created_affiliates),
                "data": created_affiliates,
                "credentials": credentials,
            }
        except Exception as e:
            self.db.rollback()
            raise e


class ShippingCommissionPaymentSeeder(BaseSeeder):
    """배송담당자 커미션 지급 Seeder"""

    def seed(self, partners_result: Dict = None, orders_result: Dict = None) -> Dict[str, Any]:
        """
        배송담당자 커미션 지급 데이터 생성

        배송담당자 1 (NCR): 미지급 상태의 커미션 (지급 예정액 있음)
        배송담당자 2 (Visayas): 지급 데이터 없음 (지급 예정액 없음)
        """
        if not partners_result or "data" not in partners_result:
            raise ValueError("ShippingCommissionPayment 생성을 위해 먼저 FulfillmentPartner를 생성해야 합니다.")

        partners_dict = partners_result["data"]
        created_payments = []

        # 배송담당자 1 (NCR)의 처리 주문들로부터 미지급 커미션 계산
        partner_1_name = "조선미녀 필리핀 배송담당자 - NCR"
        if partner_1_name in partners_dict:
            partner_1 = partners_dict[partner_1_name]

            # 배송담당자 1은 preparing과 in_transit 상태의 주문 6개를 처리
            # 각 주문당 20 USD의 커미션 = 총 120 USD의 미지급 커미션
            total_commission = Decimal("120.00")  # 6개 주문 * 20 USD

            payment = ShippingCommissionPayment(
                id=uuid4(),
                fulfillment_partner_id=partner_1.id,
                amount=total_commission,
                status="pending",
                payment_method="PayPal",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(payment)
            created_payments.append(payment)

        # 배송담당자 2 (Visayas): 아무 지급 데이터도 생성하지 않음
        # (이미 배송 완료된 주문들이지만, 지급 예정액이 없다는 시나리오)

        self.commit()

        return {
            "type": "shipping_commission_payments",
            "count": len(created_payments),
            "data": created_payments,
        }


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
