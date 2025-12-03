#!/usr/bin/env python3
"""관리자 계정 생성 CLI 스크립트"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.persistence.database import SessionLocal
from src.persistence.models import User
from src.workflow.services.admin_service import AdminService
from src.utils.exceptions import AuthenticationError


def create_admin(email: str, password: str) -> bool:
    """
    관리자 계정 생성

    Args:
        email: 관리자 이메일
        password: 관리자 비밀번호

    Returns:
        성공 여부
    """
    db = SessionLocal()

    try:
        print(f"\n{'='*60}")
        print(f"  관리자 계정 생성")
        print(f"{'='*60}\n")

        # 이메일 중복 확인
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"❌ 오류: 이메일 '{email}'은(는) 이미 등록되어 있습니다.")
            return False

        # 관리자 생성
        print(f"📝 관리자 계정을 생성 중입니다...")
        print(f"   - 이메일: {email}")
        print(f"   - 역할: admin")

        user = AdminService.create_user(
            db=db,
            email=email,
            password=password,
            role="admin",
        )

        print(f"\n✅ 성공! 관리자 계정이 생성되었습니다.")
        print(f"\n{'─'*60}")
        print(f"  계정 정보")
        print(f"{'─'*60}")
        print(f"  사용자 ID: {user.id}")
        print(f"  이메일:    {user.email}")
        print(f"  역할:      {user.role}")
        print(f"{'─'*60}\n")

        return True

    except AuthenticationError as e:
        print(f"\n❌ 오류: {e.message}")
        return False

    except Exception as e:
        print(f"\n❌ 오류: 관리자 계정 생성 중 예상치 못한 오류가 발생했습니다.")
        print(f"   오류 메시지: {str(e)}")
        return False

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="관리자 계정을 생성합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  uv run python scripts/create_admin.py --email admin@example.com --password mypassword
  uv run python scripts/create_admin.py --email nadle --password 0000
        """,
    )

    parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="관리자 이메일 (또는 사용자명)",
    )

    parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="관리자 비밀번호",
    )

    args = parser.parse_args()

    # 관리자 생성
    success = create_admin(email=args.email, password=args.password)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
