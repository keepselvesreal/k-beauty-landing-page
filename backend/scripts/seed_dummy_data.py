"""더미 데이터 생성 스크립트 - 개별 또는 조합으로 실행 가능"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.persistence.database import SessionLocal
from src.persistence.models import Product, ShippingRate, User, FulfillmentPartner, Customer, Order
from scripts.seeders import (
    ProductSeeder,
    UserSeeder,
    FulfillmentPartnerSeeder,
    ShippingRateSeeder,
    CustomerSeeder,
    InventorySeeder,
    OrderSeeder,
    AffiliateSeeder,
    RefundSeeder,
)


def print_separator(title: str = ""):
    """구분선 출력"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")


def print_result(result: dict):
    """Seeder 결과 출력"""
    print(f"✅ {result['type'].upper()}: {result['count']}개 생성됨")

    if result["type"] == "products":
        for sku, product in result["data"].items():
            print(f"  • {product.name}")
            print(f"    ID: {product.id}")
            print(f"    SKU: {sku}")
            print(f"    가격: ${product.price}\n")

    elif result["type"] == "users":
        for name, creds in result["credentials"].items():
            print(f"  • {name}")
            print(f"    📧 Email: {creds['email']}")
            print(f"    🔑 Password: {creds['password']}")
            print(f"    ID: {creds['user_id']}\n")

    elif result["type"] == "fulfillment_partners":
        for name, partner in result["data"].items():
            print(f"  • {name}")
            print(f"    지역: {partner.region}")
            print(f"    주소: {partner.address}")
            print(f"    ID: {partner.id}\n")

    elif result["type"] == "shipping_rates":
        for region, rate in result["data"].items():
            print(f"  • {region}: ${rate.fee}\n")

    elif result["type"] == "customers":
        for customer in result["data"]:
            print(f"  • {customer.name}")
            print(f"    Email: {customer.email}")
            print(f"    Phone: {customer.phone}")
            print(f"    Region: {customer.region}")
            print(f"    ID: {customer.id}\n")

    elif result["type"] == "inventory":
        print(f"  📊 총 재고: {result['total_quantity']}개\n")
        for inv in result["data"]:
            print(f"  • {inv.partner.name}: {inv.allocated_quantity}개")

    elif result["type"] == "orders":
        for order in result["data"]:
            print(f"  • {order.order_number}")
            print(f"    고객: {order.customer.name} ({order.customer.email})")
            print(f"    상품가: ${order.subtotal}")
            print(f"    배송료: ${order.shipping_fee}")
            print(f"    총액: ${order.total_price}")
            print(f"    상태: {order.shipping_status}")
            print(f"    ID: {order.id}\n")

    elif result["type"] == "influencer":
        creds = result["credentials"]
        print(f"  • {creds['email']}")
        print(f"    📧 Email: {creds['email']}")
        print(f"    🔑 Password: {creds['password']}")
        print(f"    📝 Affiliate Code: {creds['affiliate_code']}")
        print(f"    ID: {creds['user_id']}\n")
        print(f"  테스트 데이터:")
        print(f"    • 클릭 수: 150")
        print(f"    • 판매 건수: 5")
        print(f"    • 누적 수익: ₱80.00 (16 × 5)")
        print(f"    • 지급 완료: ₱30.00")
        print(f"    • 지급 예상: ₱50.00 (80 - 30)\n")

    elif result["type"] == "refunds":
        for order in result["data"]:
            print(f"  • {order.order_number}")
            print(f"    환불 ID: REF-{order.order_number.split('-')[1]}")
            print(f"    고객: {order.customer.name}")
            print(f"    환불 사유: {order.refund_reason}")
            print(f"    요청 상태: {order.refund_status}")
            print(f"    요청 날짜: {order.refund_requested_at}\n")


def check_existing_data(db):
    """기존 데이터 확인"""
    existing_product = db.query(Product).first()
    existing_shipping = db.query(ShippingRate).first()
    existing_user = db.query(User).first()

    if existing_product or existing_shipping or existing_user:
        print("⚠️  데이터베이스에 기존 데이터가 있습니다.")
        print("\n기존 상품:")
        products = db.query(Product).all()
        for product in products[:5]:  # 처음 5개만
            print(f"  • {product.name} (ID: {product.id})")
        if len(products) > 5:
            print(f"  ... 등 {len(products) - 5}개 더")

        return True
    return False


def seed_all(db):
    """모든 더미 데이터 생성 (조합 방식)"""
    results = {}

    print_separator("1️⃣  상품 생성 중...")
    product_seeder = ProductSeeder(db)
    results["products"] = product_seeder.seed()
    print_result(results["products"])

    print_separator("2️⃣  배송담당자 사용자 생성 중...")
    user_seeder = UserSeeder(db)
    results["users"] = user_seeder.seed()
    print_result(results["users"])

    print_separator("3️⃣  배송담당자 정보 생성 중...")
    partner_seeder = FulfillmentPartnerSeeder(db)
    results["partners"] = partner_seeder.seed(results["users"])
    print_result(results["partners"])

    print_separator("4️⃣  배송료 생성 중...")
    rate_seeder = ShippingRateSeeder(db)
    results["rates"] = rate_seeder.seed()
    print_result(results["rates"])

    print_separator("5️⃣  고객 생성 중...")
    customer_seeder = CustomerSeeder(db)
    results["customers"] = customer_seeder.seed()
    print_result(results["customers"])

    print_separator("6️⃣  재고 할당 중...")
    inventory_seeder = InventorySeeder(db)
    results["inventory"] = inventory_seeder.seed(
        results["partners"], results["products"]
    )
    print_result(results["inventory"])

    print_separator("7️⃣  주문 생성 중...")
    order_seeder = OrderSeeder(db)
    results["orders"] = order_seeder.seed(
        results["customers"], results["partners"], results["products"]
    )
    print_result(results["orders"])

    print_separator("8️⃣  인플루언서 테스트 계정 생성 중...")
    affiliate_seeder = AffiliateSeeder(db)
    results["influencer"] = affiliate_seeder.seed()
    print_result(results["influencer"])

    print_separator("9️⃣  환불 요청 데이터 생성 중...")
    refund_seeder = RefundSeeder(db)
    results["refunds"] = refund_seeder.seed(results["orders"])
    print_result(results["refunds"])

    print_separator("✅ 모든 더미 데이터 생성 완료!")


def main():
    parser = argparse.ArgumentParser(
        description="더미 데이터 생성 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 모든 데이터 생성 (인플루언서 포함)
  python -m scripts.seed_dummy_data --all

  # 개별 생성
  python -m scripts.seed_dummy_data --products
  python -m scripts.seed_dummy_data --users
  python -m scripts.seed_dummy_data --partners
  python -m scripts.seed_dummy_data --influencer

  # 조합으로 생성
  python -m scripts.seed_dummy_data --products --users --partners
  python -m scripts.seed_dummy_data --customers --orders
  python -m scripts.seed_dummy_data --all --influencer
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="모든 더미 데이터 생성 (products, users, partners, rates, customers, inventory, orders)",
    )
    parser.add_argument("--products", action="store_true", help="상품 생성")
    parser.add_argument("--users", action="store_true", help="배송담당자 사용자 생성")
    parser.add_argument(
        "--partners", action="store_true", help="배송담당자 정보 생성 (users 필요)"
    )
    parser.add_argument("--shipping-rates", action="store_true", help="배송료 생성")
    parser.add_argument("--customers", action="store_true", help="고객 생성")
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="재고 할당 생성 (products, partners 필요)",
    )
    parser.add_argument(
        "--orders",
        action="store_true",
        help="주문 생성 (customers, partners, products 필요)",
    )
    parser.add_argument(
        "--influencer",
        action="store_true",
        help="인플루언서 (어필리에이트) 테스트 계정 생성",
    )
    parser.add_argument(
        "--refunds",
        action="store_true",
        help="환불 요청 데이터 생성 (orders 필요)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="기존 데이터 확인",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        # 옵션 처리
        if args.check:
            has_data = check_existing_data(db)
            if not has_data:
                print("✅ 데이터베이스가 비어있습니다.")
            return

        if args.all:
            if check_existing_data(db):
                print("\n⚠️  기존 데이터가 있어 중단했습니다.")
                print("   데이터베이스를 초기화 후 다시 시도해주세요.")
                return

            seed_all(db)
            return

        # 개별 또는 조합 생성
        results = {}

        if args.products:
            print_separator("상품 생성 중...")
            product_seeder = ProductSeeder(db)
            results["products"] = product_seeder.seed()
            print_result(results["products"])

        if args.users:
            print_separator("배송담당자 사용자 생성 중...")
            user_seeder = UserSeeder(db)
            results["users"] = user_seeder.seed()
            print_result(results["users"])

        if args.partners:
            if "users" not in results:
                print("❌ 배송담당자 생성을 위해 먼저 --users를 실행하세요.")
                return

            print_separator("배송담당자 정보 생성 중...")
            partner_seeder = FulfillmentPartnerSeeder(db)
            results["partners"] = partner_seeder.seed(results["users"])
            print_result(results["partners"])

        if args.shipping_rates:
            print_separator("배송료 생성 중...")
            rate_seeder = ShippingRateSeeder(db)
            results["rates"] = rate_seeder.seed()
            print_result(results["rates"])

        if args.customers:
            print_separator("고객 생성 중...")
            customer_seeder = CustomerSeeder(db)
            results["customers"] = customer_seeder.seed()
            print_result(results["customers"])

        if args.inventory:
            if "products" not in results or "partners" not in results:
                print("❌ 재고 할당을 위해 먼저 --products와 --partners를 실행하세요.")
                return

            print_separator("재고 할당 중...")
            inventory_seeder = InventorySeeder(db)
            results["inventory"] = inventory_seeder.seed(
                results["partners"], results["products"]
            )
            print_result(results["inventory"])

        if args.orders:
            if (
                "customers" not in results
                or "partners" not in results
                or "products" not in results
            ):
                print("❌ 주문 생성을 위해 먼저 --customers, --partners, --products를 실행하세요.")
                return

            print_separator("주문 생성 중...")
            order_seeder = OrderSeeder(db)
            results["orders"] = order_seeder.seed(
                results["customers"], results["partners"], results["products"]
            )
            print_result(results["orders"])

        if args.influencer:
            print_separator("인플루언서 테스트 계정 생성 중...")
            affiliate_seeder = AffiliateSeeder(db)
            results["influencer"] = affiliate_seeder.seed()
            print_result(results["influencer"])

        if args.refunds:
            if "orders" not in results:
                print("❌ 환불 요청 생성을 위해 먼저 --orders를 실행하세요.")
                return

            print_separator("환불 요청 데이터 생성 중...")
            refund_seeder = RefundSeeder(db)
            results["refunds"] = refund_seeder.seed(results["orders"])
            print_result(results["refunds"])

        if not any([
            args.products,
            args.users,
            args.partners,
            args.shipping_rates,
            args.customers,
            args.inventory,
            args.orders,
            args.influencer,
            args.refunds,
        ]):
            parser.print_help()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
