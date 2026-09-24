from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    onboarding_completed: bool
    preferred_theme: str
    preferred_language: str

    model_config = {"from_attributes": True}


class PatchMeRequest(BaseModel):
    display_name: str | None = None
    onboarding_completed: bool | None = None
    preferred_theme: str | None = None
    preferred_language: str | None = None
