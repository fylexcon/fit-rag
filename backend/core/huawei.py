import httpx
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import User
from core.config import settings
from core.crypto import encrypt_token, decrypt_token

HUAWEI_TOKEN_URL = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"

async def exchange_code_for_token(code: str) -> dict:
    """Exchanges an authorization code for an access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            HUAWEI_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.HUAWEI_CLIENT_ID,
                "client_secret": settings.HUAWEI_CLIENT_SECRET,
                "code": code,
                "redirect_uri": "http://localhost:8000/auth/huawei/callback",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json()

async def refresh_huawei_token_if_needed(user: User, db: AsyncSession) -> str | None:
    """Refreshes the Huawei access token if it's expired or about to expire."""
    if not user.huawei_auth:
        return None

    expires_at = user.huawei_auth.get("expires_at")
    if expires_at:
        # Check if expired or expiring in less than 5 minutes
        if datetime.utcnow().timestamp() < (expires_at - 300):
            return decrypt_token(user.huawei_auth["access_token"])

    refresh_token_enc = user.huawei_auth.get("refresh_token")
    if not refresh_token_enc:
        return None

    refresh_token = decrypt_token(refresh_token_enc)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            HUAWEI_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": settings.HUAWEI_CLIENT_ID,
                "client_secret": settings.HUAWEI_CLIENT_SECRET,
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            # Handle failure, maybe clear auth or raise
            return None

        data = response.json()
        
        new_access_token = data.get("access_token")
        new_refresh_token = data.get("refresh_token", refresh_token)
        expires_in = data.get("expires_in", 3600)
        
        user.huawei_auth = {
            "access_token": encrypt_token(new_access_token),
            "refresh_token": encrypt_token(new_refresh_token),
            "expires_at": datetime.utcnow().timestamp() + expires_in
        }
        
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return new_access_token
