"""배송담당자 주문 시드 데이터 생성"""

from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.persistence.database import SessionLocal, Base, engine
from src.persistence.models import (
    User,
    Customer,
    Product,
    FulfillmentPartner,
    PartnerAllocatedInventory,
    Order,
    OrderItem,
    ShippingRate,
)


def seed_data():
    """시드 데이터 생성"""
    db = SessionLocal()

    try:
        # 테이블 생성 (없으면)
        Base.metadata.create_all(bind=engine)

        # 배송료 데이터 (없으면)
        existing_rates = db.query(ShippingRate).count()
        if existing_rates == 0:
            rates = [
                ShippingRate(region="NCR", fee=Decimal("100.00")),
                ShippingRate(region="Luzon", fee=Decimal("120.00")),
                ShippingRate(region="Visayas", fee=Decimal("140.00")),
                ShippingRate(region="Mindanao", fee=Decimal("160.00")),
            ]
            db.add_all(rates)
            db.commit()
            print("✅ 배송료 데이터 추가 완료")

        # 배송담당자 User 및 Partner 생성
        existing_partners = db.query(FulfillmentPartner).count()
        if existing_partners == 0:
            # User 생성
            user1 = User(
                email="ncr.partner@example.com",
                password_hash="ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # password123 (SHA256)
                role="fulfillment_partner",
            )
            db.add(user1)
            db.commit()
            db.refresh(user1)

            # FulfillmentPartner 생성
            partner1 = FulfillmentPartner(
                user_id=user1.id,
                name="NCR Fulfillment Hub",
                email="ncr.partner@example.com",
                phone="+63-2-1234-5678",
                address="123 Manila Warehouse, NCR",
                region="NCR",
                is_active=True,
            )
            db.add(partner1)
            db.commit()
            db.refresh(partner1)
            print(f"✅ 배송담당자 생성: {partner1.name}")

            # 상품 생성
            products = [
                Product(
                    name="조선미녀 맑은쌀 선크림 50ml",
                    description="K-Beauty 프리미엄 라이스 선크림",
                    price=Decimal("45.00"),
                    sku="KBRC-001",
                    image_url="https://via.placeholder.com/300x300?text=Rice+Sunscreen",
                    is_active=True,
                ),
                Product(
                    name="비타민C 에센스 30ml",
                    description="비타민C 집중 에센스",
                    price=Decimal("35.00"),
                    sku="KBVC-001",
                    image_url="https://via.placeholder.com/300x300?text=Vitamin+C",
                    is_active=True,
                ),
                Product(
                    name="화이트닝 마스크팩 10장",
                    description="화이트닝 시트 마스크",
                    price=Decimal("25.00"),
                    sku="KBWM-001",
                    image_url="https://via.placeholder.com/300x300?text=Mask+Pack",
                    is_active=True,
                ),
            ]
            db.add_all(products)
            db.commit()
            for p in products:
                db.refresh(p)
            print(f"✅ 상품 {len(products)}개 생성 완료")

            # 배송담당자 재고 할당
            for product in products:
                inventory = PartnerAllocatedInventory(
                    partner_id=partner1.id,
                    product_id=product.id,
                    allocated_quantity=100,
                    remaining_quantity=100,
                    stock_version=0,
                )
                db.add(inventory)
            db.commit()
            print("✅ 배송담당자 재고 할당 완료")

            # 고객 생성
            customers = [
                Customer(
                    email="customer1@example.com",
                    name="Maria Santos",
                    phone="+63-9171234567",
                    address="Manila, Philippines",
                    region="NCR",
                ),
                Customer(
                    email="customer2@example.com",
                    name="Juan Dela Cruz",
                    phone="+63-9171234568",
                    address="Quezon City, Philippines",
                    region="NCR",
                ),
                Customer(
                    email="customer3@example.com",
                    name="Ana Garcia",
                    phone="+63-9171234569",
                    address="Makati City, Philippines",
                    region="NCR",
                ),
            ]
            db.add_all(customers)
            db.commit()
            for c in customers:
                db.refresh(c)
            print(f"✅ 고객 {len(customers)}명 생성 완료")

            # 주문 생성 (preparing 상태)
            now = datetime.utcnow()
            orders_data = [
                # preparing 상태 주문들
                {
                    "customer": customers[0],
                    "product": products[0],
                    "quantity": 2,
                    "status": "preparing",
                    "created_at": now - timedelta(hours=2),
                },
                {
                    "customer": customers[1],
                    "product": products[1],
                    "quantity": 1,
                    "status": "preparing",
                    "created_at": now - timedelta(hours=1),
                },
                {
                    "customer": customers[2],
                    "product": products[2],
                    "quantity": 3,
                    "status": "preparing",
                    "created_at": now - timedelta(minutes=30),
                },
                # shipped 상태 주문 (참고용)
                {
                    "customer": customers[0],
                    "product": products[1],
                    "quantity": 1,
                    "status": "shipped",
                    "created_at": now - timedelta(hours=5),
                },
            ]

            for order_data in orders_data:
                customer = order_data["customer"]
                product = order_data["product"]
                quantity = order_data["quantity"]
                status = order_data["status"]
                created_at = order_data["created_at"]

                unit_price = product.price
                subtotal = unit_price * quantity
                shipping_fee = Decimal("100.00")  # NCR
                total_price = subtotal + shipping_fee

                order = Order(
                    order_number=f"ORD-{uuid4()}",
                    customer_id=customer.id,
                    fulfillment_partner_id=partner1.id,
                    subtotal=subtotal,
                    shipping_fee=shipping_fee,
                    total_price=total_price,
                    payment_status="completed",
                    shipping_status=status,
                    created_at=created_at,
                    updated_at=created_at,
                )
                db.add(order)
                db.commit()
                db.refresh(order)

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                )
                db.add(order_item)
                db.commit()

            print(f"✅ 주문 {len(orders_data)}개 생성 완료")
            print("\n✅ 시드 데이터 생성 완료!")
            print(f"\n로그인 정보:")
            print(f"  이메일: {user1.email}")
            print(f"  비밀번호: password123")

        else:
            print("⚠️ 이미 배송담당자 데이터가 존재합니다. 스킵합니다.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
