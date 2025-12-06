"""문의(Inquiry) 라우터 - Presentation Layer"""

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from src.persistence.database import get_db
from src.persistence.models import User, Inquiry
from src.presentation.schemas.inquiry import (
    InquiryRequest,
    InquiryResponse,
    InquiryDetailResponse,
    InquiryListResponse,
    InquiryStatusUpdateRequest,
)
from src.infrastructure.auth import JWTTokenManager
from src.infrastructure.exceptions import AuthenticationError
from src.workflow.services.inquiry_service import InquiryService

router = APIRouter(prefix="/api/inquiries", tags=["Inquiries"])


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """현재 로그인한 사용자 정보 추출

    Args:
        authorization: Authorization 헤더 (Bearer token)
        db: 데이터베이스 세션

    Returns:
        현재 사용자의 User 객체

    Raises:
        HTTPException: 토큰 없음, 유효하지 않음
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

    return user


def get_optional_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
) -> User | None:
    """선택적 사용자 정보 추출 (토큰이 없을 수도 있음)

    Args:
        authorization: Authorization 헤더 (Bearer token)
        db: 데이터베이스 세션

    Returns:
        현재 사용자의 User 객체 또는 None
    """
    if not authorization:
        return None

    # Bearer 토큰 추출
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]

    # JWT 토큰 검증
    try:
        payload = JWTTokenManager.verify_access_token(token)
    except AuthenticationError:
        return None

    # 사용자 조회
    user_id = payload.get("user_id")
    user = db.query(User).filter(User.id == user_id).first()
    return user


@router.post("", response_model=InquiryResponse)
async def create_inquiry(
    request: InquiryRequest,
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """문의 생성 (모든 사용자)

    Request:
    {
        "inquiry_type": "influencer|fulfillment_partner|customer",
        "message": "문의 내용",
        "reply_to_email": "optional@example.com" (생략 시 자동 채우기)
    }

    Response:
    {
        "status": "sent",
        "message": "문의가 발송되었습니다",
        "inquiry_id": "uuid"
    }
    """
    try:
        # 1. 메시지 검증
        if not request.message or not request.message.strip():
            raise ValueError("메시지 내용이 비어있습니다")

        # 2. 회신받을 이메일 결정
        reply_to_email = request.reply_to_email

        if not reply_to_email:
            # 자동 채우기 로직
            if request.inquiry_type == "influencer":
                if not current_user:
                    raise ValueError("인플루언서는 로그인이 필요합니다")
                reply_to_email = InquiryService.get_affiliate_email_by_user_id(
                    current_user.id, db
                )
                if not reply_to_email:
                    raise ValueError("인플루언서 정보를 찾을 수 없습니다")

            elif request.inquiry_type == "fulfillment_partner":
                if not current_user:
                    raise ValueError("배송담당자는 로그인이 필요합니다")
                reply_to_email = InquiryService.get_fulfillment_partner_email_by_user_id(
                    current_user.id, db
                )
                if not reply_to_email:
                    raise ValueError("배송담당자 정보를 찾을 수 없습니다")

            elif request.inquiry_type == "customer":
                raise ValueError("고객의 경우 회신받을 이메일을 입력해주세요")

            else:
                raise ValueError(f"유효하지 않은 문의 타입: {request.inquiry_type}")

        # 3. 문의 생성
        inquiry = InquiryService.create_inquiry(
            db=db,
            inquiry_type=request.inquiry_type,
            message=request.message.strip(),
            reply_to_email=reply_to_email,
            sender_id=current_user.id if current_user else None,
        )

        return InquiryResponse(
            status="sent",
            message="문의가 저장되었습니다",
            inquiry_id=inquiry.id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": str(e),
            },
        )
    except Exception as e:
        return InquiryResponse(
            status="failed",
            message=f"문의 저장 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/admin/list", response_model=InquiryListResponse)
async def get_inquiries(
    page: int = 1,
    page_size: int = 20,
    inquiry_type: str | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """관리자용 문의 목록 조회 (페이지네이션, 필터링)

    Query Parameters:
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지 크기 (기본값: 20)
    - inquiry_type: 필터 - 문의 타입 (influencer, fulfillment_partner, customer)
    - status_filter: 필터 - 상태 (unread, read)

    Returns:
    {
        "total": 100,
        "page": 1,
        "page_size": 20,
        "inquiries": [
            {
                "id": "uuid",
                "inquiry_type": "customer",
                "sender_id": "uuid",
                "reply_to_email": "user@example.com",
                "message": "문의 내용",
                "status": "unread",
                "created_at": "2025-12-03T12:00:00",
                "updated_at": "2025-12-03T12:00:00"
            }
        ]
    }
    """
    try:
        # 관리자 권한 확인 (role이 admin인지 확인)
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSION",
                    "message": "관리자 권한이 필요합니다",
                },
            )

        # 문의 목록 조회
        inquiries, total = InquiryService.get_all_inquiries(
            db=db,
            page=page,
            page_size=page_size,
            inquiry_type=inquiry_type,
            status=status_filter,
        )

        return InquiryListResponse(
            total=total,
            page=page,
            page_size=page_size,
            inquiries=[
                InquiryDetailResponse.from_orm(inquiry) for inquiry in inquiries
            ],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"오류가 발생했습니다: {str(e)}",
            },
        )


@router.patch("/admin/{inquiry_id}/status", response_model=InquiryDetailResponse)
async def update_inquiry_status(
    inquiry_id: str,
    request: InquiryStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """관리자용 문의 상태 변경

    Path Parameters:
    - inquiry_id: 문의 ID

    Request:
    {
        "status": "read|unread"
    }

    Returns:
    {
        "id": "uuid",
        "inquiry_type": "customer",
        "sender_id": "uuid",
        "reply_to_email": "user@example.com",
        "message": "문의 내용",
        "status": "read",
        "created_at": "2025-12-03T12:00:00",
        "updated_at": "2025-12-03T12:00:00"
    }
    """
    try:
        # 관리자 권한 확인
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "INSUFFICIENT_PERMISSION",
                    "message": "관리자 권한이 필요합니다",
                },
            )

        # 문의 조회
        inquiry = InquiryService.get_inquiry_by_id(db, inquiry_id)
        if not inquiry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NOT_FOUND",
                    "message": "문의를 찾을 수 없습니다",
                },
            )

        # 상태 변경
        updated_inquiry = InquiryService.update_inquiry_status(
            db=db,
            inquiry_id=inquiry_id,
            status=request.status,
        )

        return InquiryDetailResponse.from_orm(updated_inquiry)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": f"오류가 발생했습니다: {str(e)}",
            },
        )
