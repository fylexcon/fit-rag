import json
import uuid
from datetime import datetime, time, timedelta, timezone
from typing import Any

from bson.errors import InvalidId
from sqlalchemy import Date, case, cast, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.models import Activity
from core.mongo import get_raw_activity

SLEEP_ACTIVITY_TYPE = "sleep"
# Keys under which a raw payload may carry per-sample time series.
STREAM_KEYS = ("samples", "samplePoints")


async def list_activities(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 20, offset: int = 0
) -> tuple[list[Activity], int]:
    """Returns a page of the user's activities (newest first) and the total count."""
    total = await db.scalar(
        select(func.count()).select_from(Activity).where(Activity.user_id == user_id)
    )
    result = await db.execute(
        select(Activity)
        .where(Activity.user_id == user_id)
        .order_by(Activity.start_time.desc(), Activity.id)
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all()), total or 0


async def get_activity_detail(
    db: AsyncSession, activity_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Activity, dict | None] | None:
    """Fetches an activity owned by the user, joined with its raw MongoDB document.

    Returns None if the activity does not exist or belongs to another user.
    """
    result = await db.execute(
        select(Activity).where(Activity.id == activity_id, Activity.user_id == user_id)
    )
    activity = result.scalars().first()
    if activity is None:
        return None

    raw = None
    if activity.mongo_ref_id:
        try:
            raw_doc = await get_raw_activity(activity.mongo_ref_id)
        except InvalidId:
            raw_doc = None
        if raw_doc is not None:
            raw = _serialize_raw_doc(raw_doc)
    return activity, raw


async def get_health_summary(
    db: AsyncSession, user_id: uuid.UUID, days: int = 7
) -> dict:
    """Aggregates daily sleep, steps and resting heart rate over the last `days` UTC days."""
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days - 1)
    window_start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    window_end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc)

    day = cast(func.timezone("UTC", Activity.start_time), Date).label("day")
    is_sleep = func.lower(Activity.activity_type) == SLEEP_ACTIVITY_TYPE
    result = await db.execute(
        select(
            day,
            func.sum(case((is_sleep, Activity.duration_minutes))).label("sleep_minutes"),
            func.sum(Activity.steps).label("steps"),
            func.avg(Activity.resting_heart_rate).label("resting_heart_rate"),
        )
        .where(
            Activity.user_id == user_id,
            Activity.start_time >= window_start,
            Activity.start_time < window_end,
        )
        .group_by(day)
    )
    rows = {row.day: row for row in result}

    daily = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        row = rows.get(d)
        daily.append({
            "date": d,
            "sleep_hours": round(row.sleep_minutes / 60, 2) if row and row.sleep_minutes is not None else None,
            "steps": int(row.steps) if row and row.steps is not None else None,
            "resting_heart_rate": round(float(row.resting_heart_rate), 1) if row and row.resting_heart_rate is not None else None,
        })

    sleep_values = [m["sleep_hours"] for m in daily if m["sleep_hours"] is not None]
    step_values = [m["steps"] for m in daily if m["steps"] is not None]
    rhr_values = [m["resting_heart_rate"] for m in daily if m["resting_heart_rate"] is not None]

    return {
        "days": days,
        "start_date": start_date,
        "end_date": end_date,
        "daily": daily,
        "avg_sleep_hours": round(sum(sleep_values) / len(sleep_values), 2) if sleep_values else None,
        "total_steps": sum(step_values) if step_values else None,
        "avg_resting_heart_rate": round(sum(rhr_values) / len(rhr_values), 1) if rhr_values else None,
    }


def _serialize_raw_doc(doc: dict) -> dict:
    source = doc.get("source", "unknown")
    raw_input = doc.get("raw_input")
    has_image = source == "manual_image"

    if has_image:
        # The base64 screenshot can be megabytes; never ship it back in the detail view.
        payload = None
    else:
        payload = _try_parse_json(raw_input)

    return {
        "id": str(doc["_id"]),
        "source": source,
        "created_at": doc.get("created_at"),
        "payload": payload,
        "extracted": _try_parse_json(doc.get("extracted_json")),
        "has_image": has_image,
        "streams": _extract_streams(payload) if isinstance(payload, dict) else [],
    }


def _try_parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return value


def _extract_streams(payload: dict) -> list[dict]:
    """Normalizes per-sample data into points keyed by seconds since the first sample.

    Each sample may carry `timestamp`/`startTime` (epoch ms) or `offsetSec`, plus
    `heartRate` and either `pace` (min/km) or `speed` (m/s).
    """
    samples = next(
        (payload[k] for k in STREAM_KEYS if isinstance(payload.get(k), list)), []
    )
    samples = [s for s in samples if isinstance(s, dict)]
    timestamps = [
        s.get("timestamp", s.get("startTime"))
        for s in samples
        if s.get("timestamp", s.get("startTime")) is not None
    ]
    first_ts = min(timestamps) if timestamps else None

    points = []
    for sample in samples:
        if "offsetSec" in sample:
            elapsed = float(sample["offsetSec"])
        else:
            ts = sample.get("timestamp", sample.get("startTime"))
            if ts is None:
                continue
            elapsed = (ts - first_ts) / 1000.0

        pace = sample.get("pace")
        speed = sample.get("speed")
        if pace is None and speed:
            pace = 1000.0 / (speed * 60.0)

        heart_rate = sample.get("heartRate")
        if heart_rate is None and pace is None:
            continue
        points.append({
            "elapsed_sec": elapsed,
            "heart_rate": heart_rate,
            "pace_min_per_km": round(pace, 2) if pace is not None else None,
        })
    points.sort(key=lambda p: p["elapsed_sec"])
    return points
