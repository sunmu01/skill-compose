"""
Simple shared-password JWT authentication.

[INPUT]: 环境变量 AUTH_PASSWORD, JWT_SECRET
[OUTPUT]: 对外提供 login/verify 路由, require_auth 依赖, verify_token/create_token 工具函数
[POS]: api/v1 的认证守门员，被 main.py AuthMiddleware 和前端 login 页面消费
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# ── 极简 JWT (HS256, 零外部依赖) ────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def _get_secret() -> str:
    return os.environ.get("JWT_SECRET", "change-me-in-production")


def create_token(expires_hours: int = 720) -> str:
    """生成 JWT token，默认 30 天有效"""
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "sub": "admin",
        "exp": int(time.time()) + expires_hours * 3600,
    }).encode())
    sig = _b64url_encode(hmac.new(
        _get_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256
    ).digest())
    return f"{header}.{payload}.{sig}"


def verify_token(token: str) -> dict:
    """验证 JWT token 签名和过期时间"""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")
    header, payload, sig = parts
    expected = _b64url_encode(hmac.new(
        _get_secret().encode(), f"{header}.{payload}".encode(), hashlib.sha256
    ).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("Invalid signature")
    data = json.loads(_b64url_decode(payload))
    if data.get("exp", 0) < time.time():
        raise ValueError("Token expired")
    return data


# ── FastAPI 依赖注入 ────────────────────────────────────────

security = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """路由级认证依赖（可选用，当前主要由 AuthMiddleware 全局拦截）"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        verify_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ── 路由 ────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    token: str


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    expected = os.environ.get("AUTH_PASSWORD", "")
    if not expected:
        raise HTTPException(500, "AUTH_PASSWORD not configured")
    if not hmac.compare_digest(req.password, expected):
        raise HTTPException(401, "Invalid password")
    return TokenResponse(token=create_token())


@router.get("/verify")
async def verify(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(401, "No token provided")
    try:
        verify_token(credentials.credentials)
        return {"valid": True}
    except ValueError:
        raise HTTPException(401, "Invalid or expired token")
