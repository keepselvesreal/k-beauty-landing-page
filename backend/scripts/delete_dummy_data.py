"""더미 데이터 삭제 스크립트"""

import argparse
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.persistence.database import SessionLocal
from src.persistence.models import (
    Order, OrderItem, Shipment, ShipmentAllocation,
    Customer, Affiliate, AffiliateClick, AffiliateSale, AffiliatePayment,
    PartnerAllocatedInventory, Product, ShippingRate,
    FulfillmentPartner, User, ShippingCommissionPayment,
    InventoryAdjustmentLog, EmailLog, AffiliateErrorLog, Inquiry
)


def print_separator(title: str = ""):
    """구분선 출력"""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}\n")


def delete_all_data(db):
    """모든 더미 데이터 삭제"""
    print_separator("🗑️  모든 더미 데이터 삭제 중...")

    tables_to_clear = [
        (AffiliateClick, "affiliate clicks"),
        (AffiliateSale, "affiliate sales"),
        (EmailLog, "email logs"),
        (AffiliateErrorLog, "affiliate error logs"),
        (AffiliatePayment, "affiliate payments"),
        (Affiliate, "affiliates"),
        (OrderItem, "order_items"),
        (ShipmentAllocation, "shipment_allocations"),
        (Shipment, "shipments"),
        (Order, "orders"),
        (InventoryAdjustmentLog, "inventory adjustment logs"),
        (PartnerAllocatedInventory, "partner allocated inventory"),
        (Customer, "customers"),
        (ShippingCommissionPayment, "shipping commission payments"),
        (FulfillmentPartner, "fulfillment partners"),
        (Product, "products"),
        (ShippingRate, "shipping rates"),
        (Inquiry, "inquiries"),
    ]

    deleted_count = 0
    for model, name in tables_to_clear:
        count = db.query(model).delete()
        if count > 0:
            print(f"✅ {name}: {count}개 삭제됨")
            deleted_count += count

    # 배송담당자 사용자 삭제
    users_with_partners = db.query(User).filter(User.role == "fulfillment_partner").all()
    for user in users_with_partners:
        if user.fulfillment_partner:
            db.delete(user.fulfillment_partner)
        db.delete(user)
    deleted_partner_users = len(users_with_partners)
    if deleted_partner_users > 0:
        print(f"✅ fulfillment partner users & partners: {deleted_partner_users}명 삭제됨")
        deleted_count += deleted_partner_users

    # 인플루언서 사용자 삭제
    influencer_users = db.query(User).filter(User.role == "influencer").all()
    for user in influencer_users:
        db.delete(user)
    deleted_influencer_users = len(influencer_users)
    if deleted_influencer_users > 0:
        print(f"✅ influencer users: {deleted_influencer_users}명 삭제됨")
        deleted_count += deleted_influencer_users

    db.commit()

    print_separator(f"✅ 총 {deleted_count}개 데이터 삭제 완료!")


def delete_only_admin(db):
    """관리자 계정만 삭제"""
    admin_user = db.query(User).filter(User.email == "nadle@naver.com").first()
    if admin_user:
        db.delete(admin_user)
        db.commit()
        print("✅ 관리자 계정 삭제됨 (nadle@naver.com)\n")
    else:
        print("⚠️  관리자 계정을 찾을 수 없습니다.\n")


def main():
    parser = argparse.ArgumentParser(
        description="더미 데이터 삭제 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 모든 더미 데이터 삭제
  python -m scripts.delete_dummy_data --all

  # 관리자 계정만 삭제
  python -m scripts.delete_dummy_data --admin
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="모든 더미 데이터 삭제 (주문, 고객, 배송담당자, 상품 등)",
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="관리자 계정만 삭제 (nadle@naver.com)",
    )

    args = parser.parse_args()

    if not args.all and not args.admin:
        parser.print_help()
        return

    db = SessionLocal()

    try:
        if args.all:
            # 확인 메시지
            response = input("⚠️  모든 더미 데이터를 삭제하시겠습니까? (yes/no): ").strip().lower()
            if response != "yes":
                print("❌ 취소되었습니다.\n")
                return

            delete_all_data(db)

        if args.admin:
            delete_only_admin(db)

    except Exception as e:
        print(f"❌ 오류 발생: {e}\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
