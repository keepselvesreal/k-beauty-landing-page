"""배송료 기본값 입력 스크립트"""

from src.persistence.database import SessionLocal
from src.persistence.models import ShippingRate

def seed_shipping_rates():
    """배송료 기본값 입력"""
    db = SessionLocal()

    try:
        # 기존 배송료 확인
        existing = db.query(ShippingRate).first()
        if existing:
            print("배송료가 이미 존재합니다.")
            return

        # 배송료 기본값
        shipping_rates = [
            ShippingRate(region="NCR", fee=100),
            ShippingRate(region="Luzon", fee=120),
            ShippingRate(region="Visayas", fee=140),
            ShippingRate(region="Mindanao", fee=160),
        ]

        db.add_all(shipping_rates)
        db.commit()

        print("✅ 배송료 기본값이 입력되었습니다.")
        for rate in shipping_rates:
            print(f"  - {rate.region}: ₱{rate.fee}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_shipping_rates()
