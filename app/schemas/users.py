from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    csrf_token: str


class SessionResponse(BaseModel):
    user: UserResponse
    csrf_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class DeleteAccountRequest(BaseModel):
    password: str


# The name can change on its own. A new password needs the current password.
class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    new_password: str | None = Field(default=None, min_length=8)
    current_password: str | None = None
