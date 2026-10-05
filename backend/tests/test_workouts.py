import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient, ASGITransport
from main import app
import uuid

@pytest.mark.asyncio
async def test_manual_workout_text(monkeypatch):
    test_email = f"test_{uuid.uuid4()}@example.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={"email": test_email, "password": "pass"})
        assert response.status_code == 200
        
        login_resp = await ac.post("/auth/login", data={"username": test_email, "password": "pass"})
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        
        # Mock LLM
        class MockChoice:
            class MockMessage:
                content = '{"activity_type": "running", "duration_minutes": 25.0, "distance_km": 5.0, "avg_heart_rate": 150, "notes": "Ran 5k", "start_time": "2023-01-01T12:00:00Z"}'
            message = MockMessage()
        
        class MockResponse:
            choices = [MockChoice()]
            
        async def mock_create(*args, **kwargs):
            return MockResponse()

        monkeypatch.setattr("api.workouts.client.chat.completions.create", mock_create)
        
        # Call endpoint
        headers = {"Authorization": f"Bearer {token}"}
        workout_resp = await ac.post("/workouts/manual", data={"text": "Ran 5k in 25 mins"}, headers=headers)
        assert workout_resp.status_code == 200
        data = workout_resp.json()
        assert data["activity_type"] == "running"
        assert data["duration_minutes"] == 25.0
        assert data["distance_km"] == 5.0
