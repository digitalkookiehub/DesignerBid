from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from app.auth.jwt import validate_password_strength


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str | None = None
    role: str = "user"

    @field_validator("password")
    @classmethod
    def password_strong(cls, v: str) -> str:
        if not validate_password_strength(v):
            raise ValueError("Password must be at least 8 characters with uppercase, lowercase, and number")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    company_name: str | None
    company_address: str | None
    company_logo_url: str | None
    phone: str | None
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    role: str
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    company_name: str | None = None
    company_address: str | None = None
    phone: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str
