import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.future import select
from core.database import AsyncSessionLocal
from core.models import User, Activity
from core.mongo import client as motor_client
from tasks.huawei_tasks import async_poll_huawei_health
from datetime import datetime

HUAWEI_MOCK_PAYLOAD = {
    "activityRecords": [
        {
            "activityType": "Sleep",
            "duration": 28800, # 8 hours * 3600
            "startTime": 1700000000000,
            "endTime": 1700028800000
        },
        {
            "activityType": "Running",
            "duration": 1800, # 30 min
            "distance": 5000, # 5km
            "avgHeartRate": 150,
            "startTime": 1700100000000,
            "endTime": 1700101800000
        }
    ]
}

@pytest.mark.asyncio
async def test_huawei_polling_task():
    # 1. Create a user with connected Huawei auth
    user_email = f"huawei_test_{uuid.uuid4()}@example.com"
    user_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as db:
        user = User(
            id=user_id,
            email=user_email,
            hashed_password="mock",
            huawei_auth={
                "access_token": "mock_encrypted_access",
                "refresh_token": "mock_encrypted_refresh",
                "expires_at": datetime.utcnow().timestamp() + 3600,
                "last_synced_at": 0
            }
        )
        db.add(user)
        await db.commit()

    # 2. Mock token refresh and HTTP GET
    with patch("tasks.huawei_tasks.refresh_huawei_token_if_needed", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = "mock_access_token_decrypted"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = HUAWEI_MOCK_PAYLOAD
        
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            
            # Execute polling task
            await async_poll_huawei_health()

    # 3. Assert PostgreSQL got the normalized records
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Activity).where(Activity.user_id == user_id))
        activities = result.scalars().all()
        
        assert len(activities) == 2
        
        sleep_activity = next(a for a in activities if a.activity_type == "Sleep")
        assert sleep_activity.duration_minutes == 480.0
        assert sleep_activity.source == "huawei"
        
        run_activity = next(a for a in activities if a.activity_type == "Running")
        assert run_activity.duration_minutes == 30.0
        assert run_activity.distance_km == 5.0
        assert run_activity.avg_heart_rate == 150
        assert run_activity.source == "huawei"
        
        # Verify user last_synced_at is updated
        user_result = await db.execute(select(User).where(User.id == user_id))
        updated_user = user_result.scalars().first()
        assert updated_user.huawei_auth["last_synced_at"] > 0
        
        raw_ids = [sleep_activity.mongo_ref_id, run_activity.mongo_ref_id]

    # 4. Assert MongoDB got the raw records
    raw_collection = motor_client.fitness.raw_activities
    
    from bson.objectid import ObjectId
    for rid in raw_ids:
        doc = await raw_collection.find_one({"_id": ObjectId(rid)})
        assert doc is not None
        assert doc["source"] == "huawei"
        assert "raw_input" in doc
