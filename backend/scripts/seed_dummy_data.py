"""더미 데이터 입력 스크립트 (상품, 배송담당자, 재고, 배송료, 고객, 주문)"""

import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from decimal import Decimal

from src.persistence.database import SessionLocal
from src.persistence.models import (
    User, Product, FulfillmentPartner, PartnerAllocatedInventory, ShippingRate,
    Customer, Order, OrderItem
)
from src.workflow.services.authentication_service import AuthenticationService


def seed_dummy_data():
    """test-dummy-data.json에서 상품, 배송담당자, 재고 데이터 생성"""
    db = SessionLocal()

    try:
        # 1. 기존 데이터 확인
        existing_product = db.query(Product).first()
        existing_shipping = db.query(ShippingRate).first()
        if existing_product or existing_shipping:
            print("⚠️  데이터가 이미 존재합니다.")
            print("\n기존 상품:")
            products = db.query(Product).all()
            for product in products:
                print(f"  • {product.name} (ID: {product.id})")
            return

        # 2. test-dummy-data.json 읽기
        data_file = Path(__file__).parent.parent / "test-dummy-data.json"
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 3. 상품 생성
        products_data = data.get("products", [])
        if not products_data:
            print("❌ test-dummy-data.json에 products 데이터가 없습니다.")
            return

        created_products = {}
        for product_data in products_data:
            product = Product(
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                sku=product_data["sku"],
                image_url=product_data["image_url"],
                is_active=product_data.get("is_active", True),
            )
            db.add(product)
            created_products[product_data["sku"]] = product

        db.commit()

        # 4. 배송담당자 생성 (User와 함께)
        partners_data = data.get("fulfillment_partners", [])
        created_partners = {}
        partner_credentials = {}  # 로그인 정보 저장

        for partner_data in partners_data:
            # User 생성 (인증용)
            email = partner_data["email"]
            password = f"Partner@{partner_data['region']}123"  # 임시 비밀번호
            password_hash = AuthenticationService.hash_password(password)

            user = User(
                email=email,
                password_hash=password_hash,
                role="fulfillment_partner",
                is_active=True,
            )
            db.add(user)
            db.flush()  # user.id를 얻기 위해

            # FulfillmentPartner 생성 (user_id 연결)
            partner = FulfillmentPartner(
                user_id=user.id,
                name=partner_data["name"],
                email=partner_data["email"],
                phone=partner_data["phone"],
                address=partner_data["address"],
                region=partner_data["region"],
                is_active=partner_data.get("is_active", True),
            )
            db.add(partner)
            db.flush()

            created_partners[partner_data["name"]] = partner
            partner_credentials[partner_data["name"]] = {
                "email": email,
                "password": password,
                "user_id": str(user.id),
            }

        db.commit()

        # 5. 배송담당자별 재고 할당
        inventory_data = data.get("inventory", [])
        total_inventory = 0
        for inv_data in inventory_data:
            product_sku = inv_data["product_sku"]
            partner_name = inv_data["partner_name"]

            product = created_products.get(product_sku)
            partner = created_partners.get(partner_name)

            if product and partner:
                allocated_inv = PartnerAllocatedInventory(
                    partner_id=partner.id,
                    product_id=product.id,
                    allocated_quantity=inv_data["allocated_quantity"],
                    remaining_quantity=inv_data["remaining_quantity"],
                )
                db.add(allocated_inv)
                total_inventory += inv_data["allocated_quantity"]

        db.commit()

        # 6. 배송료 생성 (필리핀 지역별)
        shipping_rates_data = [
            {"region": "NCR", "fee": 100},
            {"region": "Luzon", "fee": 120},
            {"region": "Visayas", "fee": 140},
            {"region": "Mindanao", "fee": 160},
        ]
        for sr_data in shipping_rates_data:
            shipping_rate = ShippingRate(
                region=sr_data["region"],
                fee=sr_data["fee"],
            )
            db.add(shipping_rate)

        db.commit()

        # 7. 고객 생성
        customers_data = [
            {
                "email": "test.customer@example.com",
                "name": "테스트 고객",
                "phone": "09123456789",
                "address": "Manila, Philippines",
                "region": "NCR",
            },
            {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "phone": "09234567890",
                "address": "Quezon City, Philippines",
                "region": "NCR",
            },
            {
                "email": "jane.smith@example.com",
                "name": "Jane Smith",
                "phone": "09345678901",
                "address": "Cebu City, Philippines",
                "region": "Visayas",
            },
        ]
        created_customers = []
        for cust_data in customers_data:
            customer = Customer(
                email=cust_data["email"],
                name=cust_data["name"],
                phone=cust_data["phone"],
                address=cust_data["address"],
                region=cust_data["region"],
            )
            db.add(customer)
            created_customers.append(customer)

        db.commit()

        # 8. 샘플 주문 생성
        # 첫 번째 고객으로 주문 생성
        test_customer = created_customers[0]
        ncr_partner = created_partners['NCR Fulfillment Hub']
        product = list(created_products.values())[0]

        order = Order(
            id=uuid4(),
            order_number=f"ORD-{uuid4()}",
            customer_id=test_customer.id,
            fulfillment_partner_id=ncr_partner.id,
            subtotal=Decimal("750.00"),  # 1 * 750
            shipping_fee=Decimal("100.00"),  # NCR 배송료
            total_price=Decimal("850.00"),  # 750 + 100
            payment_status="paid",
            shipping_status="preparing",
            paypal_order_id="SAMPLE-PAYPAL-ORDER-001",
            paypal_capture_id="SAMPLE-PAYPAL-CAPTURE-001",
            paypal_fee=Decimal("25.50"),  # 3.4% 예상 수수료
            profit=Decimal("644.50"),  # 750 - 100 (배송료) - 25.50 (PayPal) - 80 (기본 이익)
            paid_at=datetime.now(),
        )
        db.add(order)
        db.flush()

        # OrderItem 생성
        order_item = OrderItem(
            id=uuid4(),
            order_id=order.id,
            product_id=product.id,
            quantity=1,
            unit_price=Decimal("750.00"),
        )
        db.add(order_item)

        db.commit()

        # 9. 생성 완료 메시지
        print("✅ 모든 더미 데이터가 생성되었습니다!\n")

        print("📦 상품 정보:")
        for sku, product in created_products.items():
            print(f"  • {product.name}")
            print(f"    ID: {product.id}")
            print(f"    SKU: {sku}")
            print(f"    가격: ₱{product.price}\n")

        print(f"🏢 배송담당자 ({len(created_partners)}개):")
        for name, partner in created_partners.items():
            creds = partner_credentials[name]
            print(f"  • {name}")
            print(f"    지역: {partner.region}")
            print(f"    ID: {partner.id}")
            print(f"    📧 로그인 이메일: {creds['email']}")
            print(f"    🔑 임시 비밀번호: {creds['password']}\n")

        print(f"📊 총 재고: {total_inventory}개")
        for inv_data in inventory_data:
            partner = created_partners[inv_data["partner_name"]]
            print(f"  • {partner.name}: {inv_data['allocated_quantity']}개")

        print(f"\n📮 배송료:")
        for sr_data in shipping_rates_data:
            print(f"  • {sr_data['region']}: ₱{sr_data['fee']}")

        print(f"\n👥 생성된 고객 ({len(created_customers)}명):")
        for customer in created_customers:
            print(f"  • {customer.name}")
            print(f"    Email: {customer.email}")
            print(f"    Phone: {customer.phone}")
            print(f"    Region: {customer.region}")
            print(f"    ID: {customer.id}\n")

        print(f"\n📦 생성된 주문 (1개):")
        print(f"  • {order.order_number}")
        print(f"    고객: {test_customer.name} ({test_customer.email})")
        print(f"    상품: {product.name} (수량: 1)")
        print(f"    상품가: ₱{order.subtotal}")
        print(f"    배송료: ₱{order.shipping_fee}")
        print(f"    총액: ₱{order.total_price}")
        print(f"    결제상태: {order.payment_status}")
        print(f"    배송상태: {order.shipping_status}")
        print(f"    주문ID: {order.id}\n")

        # 10. 프런트엔드 설정 정보
        print("\n" + "=" * 60)
        print("📋 프런트엔드 constants.ts에 다음 UUID를 사용하세요:")
        print("=" * 60)
        for sku, product in created_products.items():
            print(f"export const PRODUCT = {{")
            print(f"  id: '{product.id}',")
            print(f"  // ... 나머지 필드")
            print(f"}};")

    except FileNotFoundError:
        print(f"❌ test-dummy-data.json 파일을 찾을 수 없습니다.")
        print(f"   경로: {Path(__file__).parent.parent / 'test-dummy-data.json'}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파일 형식이 올바르지 않습니다: {e}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_dummy_data()
