"""인플루언서 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from decimal import Decimal

from src.persistence.database import get_db
from src.persistence.models import User, Affiliate, AffiliateClick, AffiliatePayment
from src.presentation.schemas.influencer import (
    InfluencerDashboardResponse,
    AffiliateClickRequest,
    AffiliateClickResponse,
)
from src.utils.auth import JWTTokenManager
from src.utils.exceptions import AuthenticationError
from src.config import settings

router = APIRouter(prefix="/api/influencer", tags=["Influencer"])


def get_current_influencer(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> Affiliate:
    """
    현재 인플루언서 정보 추출

    Args:
        authorization: Authorization 헤더 (Bearer token)
        db: 데이터베이스 세션

    Returns:
        현재 사용자의 Affiliate 객체

    Raises:
        HTTPException: 토큰 없음, 유효하지 않음, 인플루언서 아님
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_TOKEN",
                "message": "Authorization 헤더가 필요합니다.",
            },
        )

    # Bearer 토큰 추출
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_FORMAT",
                "message": "유효하지 않은 토큰 형식입니다.",
            },
        )

    token = parts[1]

    # JWT 토큰 검증
    try:
        payload = JWTTokenManager.verify_access_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
        )

    # 사용자 조회
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "사용자를 찾을 수 없습니다.",
            },
        )

    # 인플루언서 조회
    affiliate = user.affiliate
    if not affiliate:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "NOT_INFLUENCER",
                "message": "인플루언서 권한이 필요합니다.",
            },
        )

    return affiliate


@router.get("/dashboard", response_model=InfluencerDashboardResponse)
async def get_influencer_dashboard(
    current_affiliate: Affiliate = Depends(get_current_influencer),
    db: Session = Depends(get_db),
):
    """
    인플루언서 대시보드 데이터 조회

    Returns:
        {
            "affiliate_code": "santa-here-kim_influencer",
            "affiliate_url": "https://example.com?aff=santa-here-kim_influencer",
            "total_clicks": 150,
            "total_sales": 5,
            "cumulative_revenue": 80.00,
            "pending_commission": 30.00,
            "next_payment_date": "2025-12-31T00:00:00"
        }
    """
    # 1. 총 클릭 수 조회
    total_clicks = db.query(AffiliateClick).filter(
        AffiliateClick.affiliate_id == current_affiliate.id
    ).count()

    # 2. 판매 건수 조회 (AffiliateSale의 개수)
    total_sales = len(current_affiliate.sales)

    # 3. 누적 수익 조회 (모든 AffiliateSale의 marketing_commission 합)
    cumulative_revenue = sum(
        sale.marketing_commission for sale in current_affiliate.sales
    ) or Decimal("0.00")

    # 4. 지급 예상 수수료 조회 (누적 수익 - 완료된 지급액)
    total_paid = sum(
        payment.amount
        for payment in current_affiliate.payments
        if payment.status == "completed"
    ) or Decimal("0.00")
    pending_commission = cumulative_revenue - total_paid

    # 5. 지급 예정 날짜 계산 (임시: 현재 날짜 + AFFILIATE_PAYMENT_DAYS)
    # 실제로는 마지막 지급 날짜 + AFFILIATE_PAYMENT_DAYS 등으로 계산 가능
    next_payment_date = datetime.utcnow() + timedelta(
        days=settings.AFFILIATE_PAYMENT_DAYS
    )

    # 6. 추적 URL 생성
    affiliate_url = f"{settings.FRONTEND_BASE_URL}?aff={current_affiliate.code}"

    return InfluencerDashboardResponse(
        affiliate_code=current_affiliate.code,
        affiliate_url=affiliate_url,
        total_clicks=total_clicks,
        total_sales=total_sales,
        cumulative_revenue=cumulative_revenue,
        pending_commission=pending_commission,
        next_payment_date=next_payment_date,
    )


@router.post("/click", response_model=AffiliateClickResponse)
async def track_affiliate_click(
    request: AffiliateClickRequest,
    db: Session = Depends(get_db),
):
    """
    어필리에이트 클릭 추적

    Request:
    {
        "code": "santa-here-kim_influencer"
    }

    Response:
    {
        "status": "success",
        "message": "클릭이 기록되었습니다"
    }
    """
    try:
        # 1. 어필리에이트 코드로 조회
        affiliate = db.query(Affiliate).filter(
            Affiliate.code == request.code
        ).first()

        if not affiliate:
            return AffiliateClickResponse(
                status="error",
                message="유효하지 않은 어필리에이트 코드입니다",
            )

        # 2. 비활성 상태 확인
        if not affiliate.is_active:
            return AffiliateClickResponse(
                status="error",
                message="비활성화된 어필리에이트입니다",
            )

        # 3. 클릭 기록 생성
        click = AffiliateClick(affiliate_id=affiliate.id)
        db.add(click)
        db.commit()

        return AffiliateClickResponse(
            status="success",
            message="클릭이 기록되었습니다",
        )

    except Exception as e:
        db.rollback()
        return AffiliateClickResponse(
            status="error",
            message=f"클릭 기록 중 오류가 발생했습니다: {str(e)}",
        )
