"""문의 비즈니스 로직 서비스"""

from uuid import UUID
from sqlalchemy.orm import Session

from src.persistence.models import Inquiry, Affiliate, FulfillmentPartner, User


class InquiryService:
    """Inquiry Service"""

    @staticmethod
    def get_user_email_by_id(user_id: UUID, db: Session) -> str | None:
        """사용자 ID로 이메일 조회

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션

        Returns:
            사용자 이메일 또는 None
        """
        user = db.query(User).filter(User.id == user_id).first()
        return user.email if user else None

    @staticmethod
    def get_affiliate_email_by_user_id(user_id: UUID, db: Session) -> str | None:
        """사용자 ID로 어필리에이트(인플루언서) 이메일 조회

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션

        Returns:
            인플루언서 이메일 또는 None
        """
        affiliate = db.query(Affiliate).filter(
            Affiliate.user_id == user_id
        ).first()
        return affiliate.email if affiliate else None

    @staticmethod
    def get_fulfillment_partner_email_by_user_id(user_id: UUID, db: Session) -> str | None:
        """사용자 ID로 배송담당자 이메일 조회

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션

        Returns:
            배송담당자 이메일 또는 None
        """
        partner = db.query(FulfillmentPartner).filter(
            FulfillmentPartner.user_id == user_id
        ).first()
        return partner.email if partner else None

    @staticmethod
    def create_inquiry(
        db: Session,
        inquiry_type: str,
        message: str,
        reply_to_email: str,
        sender_id: UUID | None = None,
    ) -> Inquiry:
        """문의 생성

        Args:
            db: 데이터베이스 세션
            inquiry_type: 문의 타입 (influencer, fulfillment_partner, customer)
            message: 문의 내용
            reply_to_email: 회신받을 이메일
            sender_id: 발신자 ID (로그인한 사용자)

        Returns:
            생성된 Inquiry 객체
        """
        inquiry = Inquiry(
            inquiry_type=inquiry_type,
            sender_id=sender_id,
            reply_to_email=reply_to_email,
            message=message,
            status="unread",
        )
        db.add(inquiry)
        db.commit()
        db.refresh(inquiry)
        return inquiry

    @staticmethod
    def get_inquiry_by_id(db: Session, inquiry_id: UUID) -> Inquiry | None:
        """ID로 문의 조회

        Args:
            db: 데이터베이스 세션
            inquiry_id: 문의 ID

        Returns:
            Inquiry 객체 또는 None
        """
        return db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()

    @staticmethod
    def get_all_inquiries(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        inquiry_type: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Inquiry], int]:
        """모든 문의 조회 (페이지네이션, 필터링)

        Args:
            db: 데이터베이스 세션
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기
            inquiry_type: 필터 - 문의 타입
            status: 필터 - 문의 상태

        Returns:
            (문의 목록, 총 개수)
        """
        query = db.query(Inquiry)

        # 필터링
        if inquiry_type:
            query = query.filter(Inquiry.inquiry_type == inquiry_type)
        if status:
            query = query.filter(Inquiry.status == status)

        # 총 개수
        total = query.count()

        # 페이지네이션
        skip = (page - 1) * page_size
        inquiries = query.order_by(Inquiry.created_at.desc()).offset(skip).limit(page_size).all()

        return inquiries, total

    @staticmethod
    def update_inquiry_status(
        db: Session,
        inquiry_id: UUID,
        status: str,
    ) -> Inquiry | None:
        """문의 상태 변경

        Args:
            db: 데이터베이스 세션
            inquiry_id: 문의 ID
            status: 변경할 상태 (unread, read)

        Returns:
            변경된 Inquiry 객체 또는 None
        """
        inquiry = db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if not inquiry:
            return None

        inquiry.status = status
        db.commit()
        db.refresh(inquiry)
        return inquiry
