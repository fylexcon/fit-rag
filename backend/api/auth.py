from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.database import get_db
from core.models import User
from core.schemas import UserCreate, UserResponse, Token
from core.auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


from fastapi.responses import RedirectResponse
import urllib.parse
from core.auth import get_current_user
from core.config import settings
from core.huawei import exchange_code_for_token
from core.crypto import encrypt_token
from datetime import datetime

def build_huawei_authorize_url(user: User) -> str:
    base_url = "https://oauth-login.cloud.huawei.com/oauth2/v3/authorize"
    params = {
        "response_type": "code",
        "client_id": settings.HUAWEI_CLIENT_ID,
        "redirect_uri": "http://localhost:8000/auth/huawei/callback",
        "scope": "https://www.huawei.com/healthkit/sleep.read https://www.huawei.com/healthkit/heartrate.read",
        "state": str(user.id),
        "access_type": "offline",
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

@router.get("/huawei/connect")
async def connect_huawei(current_user: User = Depends(get_current_user)):
    """Redirects to Huawei auth URL with state."""
    return RedirectResponse(build_huawei_authorize_url(current_user))

@router.get("/huawei/authorize-url")
async def huawei_authorize_url(current_user: User = Depends(get_current_user)):
    """Returns the Huawei auth URL for SPA clients, which can't attach a Bearer token to a navigation."""
    return {"url": build_huawei_authorize_url(current_user)}

@router.get("/huawei/callback")
async def huawei_callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    """Handles the Huawei callback, gets token, encrypts and stores."""
    # state contains the user_id
    result = await db.execute(select(User).where(User.id == state))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        token_data = await exchange_code_for_token(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to exchange code")

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)

    if not access_token or not refresh_token:
        raise HTTPException(status_code=400, detail="Invalid token response")

    user.huawei_auth = {
        "access_token": encrypt_token(access_token),
        "refresh_token": encrypt_token(refresh_token),
        "expires_at": datetime.utcnow().timestamp() + expires_in
    }
    
    db.add(user)
    await db.commit()

    return {"message": "Huawei Health connected successfully"}

