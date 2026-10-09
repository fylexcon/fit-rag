import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import User
from core.auth import get_current_user
from core.schemas import (
    ActivityDetailResponse,
    ActivityListResponse,
    HealthSummaryResponse,
)
from services import activity_service

router = APIRouter(tags=["activities"])

@router.get("/activities", response_model=ActivityListResponse)
async def list_activities(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total = await activity_service.list_activities(
        db, current_user.id, limit=limit, offset=offset
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}

@router.get("/activities/{activity_id}", response_model=ActivityDetailResponse)
async def get_activity(
    activity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    detail = await activity_service.get_activity_detail(db, activity_id, current_user.id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    activity, raw = detail
    return {"activity": activity, "raw": raw}

@router.get("/health-summary", response_model=HealthSummaryResponse)
async def health_summary(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await activity_service.get_health_summary(db, current_user.id, days=days)
