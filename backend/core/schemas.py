from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ActivityCreate(BaseModel):
    source: str
    activity_type: str
    duration_minutes: float
    distance_km: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    notes: Optional[str] = None
    start_time: datetime

class ActivityResponse(ActivityCreate):
    id: UUID
    user_id: UUID

    class Config:
        from_attributes = True
