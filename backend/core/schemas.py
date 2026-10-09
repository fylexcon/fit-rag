from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Any, Optional
from datetime import date, datetime
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class ActivityCreate(BaseModel):
    source: str
    activity_type: str
    duration_minutes: float
    distance_km: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    steps: Optional[int] = None
    resting_heart_rate: Optional[int] = None
    notes: Optional[str] = None
    start_time: datetime

class ActivityResponse(ActivityCreate):
    id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True)

class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    limit: int
    offset: int

class StreamPoint(BaseModel):
    elapsed_sec: float
    heart_rate: Optional[float] = None
    pace_min_per_km: Optional[float] = None

class RawActivityPayload(BaseModel):
    id: str
    source: str
    created_at: Optional[datetime] = None
    payload: Optional[Any] = None
    extracted: Optional[Any] = None
    has_image: bool = False
    streams: list[StreamPoint] = []

class ActivityDetailResponse(BaseModel):
    activity: ActivityResponse
    raw: Optional[RawActivityPayload] = None

class DailyHealthMetric(BaseModel):
    date: date
    sleep_hours: Optional[float] = None
    steps: Optional[int] = None
    resting_heart_rate: Optional[float] = None

class HealthSummaryResponse(BaseModel):
    days: int
    start_date: date
    end_date: date
    daily: list[DailyHealthMetric]
    avg_sleep_hours: Optional[float] = None
    total_steps: Optional[int] = None
    avg_resting_heart_rate: Optional[float] = None
