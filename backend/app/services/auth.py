import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.config import settings
from app.exceptions import BadRequestError, ConflictError, NotFoundError
from app.models.user import RefreshToken, User
from app.schemas.user import TokenResponse, UserCreate, UserUpdate

logger = logging.getLogger(__name__)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def register(db: Session, data: UserCreate) -> User:
    existing = get_user_by_email(db, data.email)
    if existing:
        raise ConflictError("Email already registered")

    from app.models.user import UserRole
    role = UserRole(data.role) if data.role in ("user", "admin") else UserRole.user

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        company_name=data.company_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User registered: %s (id=%d)", user.email, user.id)
    return user


def login(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise BadRequestError("Invalid email or password")

    if not user.is_active:
        raise BadRequestError("Account is deactivated")

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token_str = create_refresh_token({"sub": str(user.id)})

    # Store refresh token
    rt = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.commit()

    logger.info("User logged in: %s", email)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


def refresh_token(db: Session, refresh_token_str: str) -> TokenResponse:
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise BadRequestError("Invalid refresh token")

    rt = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token_str,
        RefreshToken.revoked == False,  # noqa: E712
    ).first()

    if not rt:
        raise BadRequestError("Refresh token not found or revoked")

    if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise BadRequestError("Refresh token expired")

    # Revoke old token
    rt.revoked = True

    user_id = payload.get("sub")
    new_access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token({"sub": user_id})

    new_rt = RefreshToken(
        user_id=int(user_id),
        token=new_refresh,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_rt)
    db.commit()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


def logout(db: Session, user_id: int) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,  # noqa: E712
    ).update({"revoked": True})
    db.commit()
    logger.info("User logged out: id=%d", user_id)


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    logger.info("Profile updated: %s", user.email)
    return user


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)
