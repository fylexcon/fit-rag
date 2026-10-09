import json
import uuid
from datetime import datetime, time, timedelta, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from main import app
from core.database import AsyncSessionLocal
from core.models import Activity, User
from core.mongo import insert_raw_activity


async def _register_and_login(client: AsyncClient) -> tuple[uuid.UUID, dict]:
    email = f"test_activities_{uuid.uuid4()}@example.com"
    password = "password123"
    await client.post("/auth/register", json={"email": email, "password": password})
    login = await client.post("/auth/login", data={"username": email, "password": password})
    token = login.json()["access_token"]

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user_id = result.scalars().first().id
    return user_id, {"Authorization": f"Bearer {token}"}


async def _add_activities(*activities: Activity) -> list[uuid.UUID]:
    async with AsyncSessionLocal() as db:
        db.add_all(activities)
        await db.commit()
        return [a.id for a in activities]


def _activity(user_id: uuid.UUID, start_time: datetime, **kwargs) -> Activity:
    defaults = {"source": "manual_text", "activity_type": "running", "duration_minutes": 30.0}
    return Activity(user_id=user_id, start_time=start_time, **{**defaults, **kwargs})


def _today_at(hour: int, days_ago: int = 0) -> datetime:
    day = datetime.now(timezone.utc).date() - timedelta(days=days_ago)
    return datetime.combine(day, time(hour=hour), tzinfo=timezone.utc)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_activity_endpoints_require_auth(client):
    assert (await client.get("/activities")).status_code == 401
    assert (await client.get(f"/activities/{uuid.uuid4()}")).status_code == 401
    assert (await client.get("/health-summary")).status_code == 401


@pytest.mark.asyncio
async def test_list_activities_newest_first_with_pagination(client):
    user_id, headers = await _register_and_login(client)
    other_user_id, _ = await _register_and_login(client)
    now = datetime.now(timezone.utc)
    await _add_activities(
        _activity(user_id, now - timedelta(days=2), activity_type="cycling"),
        _activity(user_id, now, activity_type="running"),
        _activity(user_id, now - timedelta(days=1), activity_type="swimming"),
        _activity(other_user_id, now, activity_type="rowing"),
    )

    response = await client.get("/activities", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert [a["activity_type"] for a in data["items"]] == ["running", "swimming", "cycling"]
    assert all(a["user_id"] == str(user_id) for a in data["items"])

    page = (await client.get("/activities?limit=1&offset=1", headers=headers)).json()
    assert page["total"] == 3
    assert page["limit"] == 1 and page["offset"] == 1
    assert [a["activity_type"] for a in page["items"]] == ["swimming"]


@pytest.mark.asyncio
async def test_list_activities_rejects_invalid_pagination(client):
    _, headers = await _register_and_login(client)
    assert (await client.get("/activities?limit=0", headers=headers)).status_code == 422
    assert (await client.get("/activities?limit=101", headers=headers)).status_code == 422
    assert (await client.get("/activities?offset=-1", headers=headers)).status_code == 422


@pytest.mark.asyncio
async def test_get_activity_detail_joins_mongo_streams(client):
    user_id, headers = await _register_and_login(client)
    payload = {
        "activityType": "Running",
        "samples": [
            {"timestamp": 1700000060000, "heartRate": 150, "speed": 3.0},
            {"timestamp": 1700000000000, "heartRate": 140, "pace": 5.5},
            {"timestamp": 1700000120000},
        ],
    }
    raw_id = await insert_raw_activity(str(user_id), "huawei", json.dumps(payload))
    [activity_id] = await _add_activities(
        _activity(user_id, datetime.now(timezone.utc), source="huawei", mongo_ref_id=raw_id)
    )

    response = await client.get(f"/activities/{activity_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["activity"]["id"] == str(activity_id)
    raw = data["raw"]
    assert raw["id"] == raw_id
    assert raw["source"] == "huawei"
    assert raw["payload"]["activityType"] == "Running"
    assert raw["has_image"] is False
    # Sorted by time, relative to the first sample; samples with no values are dropped.
    assert raw["streams"] == [
        {"elapsed_sec": 0.0, "heart_rate": 140.0, "pace_min_per_km": 5.5},
        {"elapsed_sec": 60.0, "heart_rate": 150.0, "pace_min_per_km": 5.56},
    ]


@pytest.mark.asyncio
async def test_get_activity_detail_without_mongo_ref(client):
    user_id, headers = await _register_and_login(client)
    [activity_id] = await _add_activities(_activity(user_id, datetime.now(timezone.utc)))

    data = (await client.get(f"/activities/{activity_id}", headers=headers)).json()
    assert data["activity"]["id"] == str(activity_id)
    assert data["raw"] is None


@pytest.mark.asyncio
async def test_get_activity_detail_omits_screenshot_bytes(client):
    user_id, headers = await _register_and_login(client)
    raw_id = await insert_raw_activity(
        str(user_id), "manual_image", "aGVsbG8=", extracted_json='{"activity_type": "cycling"}'
    )
    [activity_id] = await _add_activities(
        _activity(user_id, datetime.now(timezone.utc), source="manual_image", mongo_ref_id=raw_id)
    )

    raw = (await client.get(f"/activities/{activity_id}", headers=headers)).json()["raw"]
    assert raw["has_image"] is True
    assert raw["payload"] is None
    assert raw["extracted"] == {"activity_type": "cycling"}
    assert raw["streams"] == []


@pytest.mark.asyncio
async def test_get_activity_detail_not_found_or_not_owned(client):
    owner_id, _ = await _register_and_login(client)
    _, intruder_headers = await _register_and_login(client)
    [activity_id] = await _add_activities(_activity(owner_id, datetime.now(timezone.utc)))

    assert (await client.get(f"/activities/{activity_id}", headers=intruder_headers)).status_code == 404
    assert (await client.get(f"/activities/{uuid.uuid4()}", headers=intruder_headers)).status_code == 404
    assert (await client.get("/activities/not-a-uuid", headers=intruder_headers)).status_code == 422


@pytest.mark.asyncio
async def test_health_summary_aggregates_daily_metrics(client):
    user_id, headers = await _register_and_login(client)
    other_user_id, _ = await _register_and_login(client)
    await _add_activities(
        # Today: two sleep records (case-insensitive type), steps and RHR from two records.
        _activity(user_id, _today_at(1), source="huawei", activity_type="Sleep", duration_minutes=360),
        _activity(user_id, _today_at(2), source="huawei", activity_type="sleep", duration_minutes=60),
        _activity(user_id, _today_at(8), steps=3000, resting_heart_rate=50),
        _activity(user_id, _today_at(9), steps=2000, resting_heart_rate=60),
        # Two days ago: sleep only.
        _activity(user_id, _today_at(1, days_ago=2), activity_type="Sleep", duration_minutes=450),
        # Outside the 7-day window and another user's data: both excluded.
        _activity(user_id, _today_at(1, days_ago=10), activity_type="Sleep", duration_minutes=600),
        _activity(other_user_id, _today_at(8), steps=99999, resting_heart_rate=99),
    )

    response = await client.get("/health-summary?days=7", headers=headers)
    assert response.status_code == 200
    data = response.json()

    today = datetime.now(timezone.utc).date()
    assert data["days"] == 7
    assert data["end_date"] == today.isoformat()
    assert data["start_date"] == (today - timedelta(days=6)).isoformat()
    assert [d["date"] for d in data["daily"]] == [
        (today - timedelta(days=6 - i)).isoformat() for i in range(7)
    ]

    by_date = {d["date"]: d for d in data["daily"]}
    assert by_date[today.isoformat()] == {
        "date": today.isoformat(),
        "sleep_hours": 7.0,
        "steps": 5000,
        "resting_heart_rate": 55.0,
    }
    two_days_ago = by_date[(today - timedelta(days=2)).isoformat()]
    assert two_days_ago["sleep_hours"] == 7.5
    assert two_days_ago["steps"] is None
    assert by_date[(today - timedelta(days=1)).isoformat()]["sleep_hours"] is None

    assert data["avg_sleep_hours"] == 7.25
    assert data["total_steps"] == 5000
    assert data["avg_resting_heart_rate"] == 55.0


@pytest.mark.asyncio
async def test_health_summary_empty_and_validation(client):
    _, headers = await _register_and_login(client)

    data = (await client.get("/health-summary", headers=headers)).json()
    assert data["days"] == 7
    assert len(data["daily"]) == 7
    assert all(d["sleep_hours"] is None and d["steps"] is None for d in data["daily"])
    assert data["avg_sleep_hours"] is None
    assert data["total_steps"] is None
    assert data["avg_resting_heart_rate"] is None

    assert (await client.get("/health-summary?days=0", headers=headers)).status_code == 422
    assert (await client.get("/health-summary?days=91", headers=headers)).status_code == 422
