"""
routes/auth.py — Authentication endpoints.

POST /api/auth/register  — create account
POST /api/auth/login     — get JWT token
GET  /api/auth/me        — get current user profile
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from database import get_db
from services.auth_service import (
    authenticate_user, create_user, decode_token,
    get_user_by_email, get_user_by_id, create_access_token,
)

router  = APIRouter()
_bearer = HTTPBearer(auto_error=False)


# ─── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    name:     str   = Field(..., min_length=2, max_length=100)
    email:    EmailStr
    password: str   = Field(..., min_length=6)
    district: str   = Field(default=None)


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      int
    name:         str
    email:        str
    district:     str | None


class UserProfile(BaseModel):
    user_id:    int
    name:       str
    email:      str
    district:   str | None
    created_at: str


# ─── Dependency — get current user from JWT ───────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token")
    user = get_user_by_id(db, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="User not found")
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Returns user if authenticated, None if not — for guest-friendly endpoints."""
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    return get_user_by_id(db, int(payload["sub"]))


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user  = create_user(db, body.name, body.email, body.password, body.district)
    token = create_access_token(user.id, user.email)
    return AuthResponse(
        access_token=token, user_id=user.id,
        name=user.name, email=user.email, district=user.district,
    )


@router.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id, user.email)
    return AuthResponse(
        access_token=token, user_id=user.id,
        name=user.name, email=user.email, district=user.district,
    )


@router.get("/auth/me", response_model=UserProfile)
def get_me(user=Depends(get_current_user)):
    return UserProfile(
        user_id    = user.id,
        name       = user.name,
        email      = user.email,
        district   = user.district,
        created_at = user.created_at.isoformat(),
    )