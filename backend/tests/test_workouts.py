import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models import Activity, User
from unittest.mock import patch, MagicMock
from core.mongo import get_raw_activity
from tasks.workout_tasks import async_process_workout

from core.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_manual_workout_text_async():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register a test user
        import uuid
        test_email = f"test_celery_{uuid.uuid4()}@example.com"
        test_password = "password123"
        await client.post("/auth/register", json={"email": test_email, "password": test_password})

        # 2. Login to get JWT
        login_response = await client.post("/auth/login", data={"username": test_email, "password": test_password})
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # 3. Get user id
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.email == test_email))
            user = result.scalars().first()
            user_id = str(user.id)

        # 4. Mock process_manual_workout_task.delay and post workout
        with patch("api.workouts.process_manual_workout_task.delay") as mock_delay:
            response = await client.post(
                "/workouts/manual",
                data={"text": "Ran 5k in 25 mins"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 202
            data = response.json()
            assert data["status"] == "processing"
            raw_id = data["raw_id"]
            
            mock_delay.assert_called_once()
            args = mock_delay.call_args[0]
            assert args[0] == raw_id

        print("Step 5")
        # 5. Check MongoDB received raw payload
        raw_doc = await get_raw_activity(raw_id)
        assert raw_doc is not None
        assert raw_doc["source"] == "manual_text"
        assert raw_doc["raw_input"] == "Ran 5k in 25 mins"
        assert raw_doc["user_id"] == user_id

        print("Step 6")
        # 6. Execute worker task manually, mocking OpenAI
        from unittest.mock import AsyncMock
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.message.content = '{"activity_type": "running", "duration_minutes": 25, "distance_km": 5}'
        mock_response.choices = [mock_message]
        
        with patch("tasks.workout_tasks.client.chat.completions.create", new_callable=AsyncMock, return_value=mock_response):
            await async_process_workout(raw_id, user_id)

        print("Step 7")
        # 7. Verify PostgreSQL updated
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Activity).where(Activity.mongo_ref_id == raw_id))
            activity = result.scalars().first()
            assert activity is not None
            assert activity.activity_type == "running"
            assert activity.duration_minutes == 25.0
            assert activity.distance_km == 5.0
