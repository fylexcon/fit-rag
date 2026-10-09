import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient, ASGITransport
from main import app
import uuid

@pytest.mark.asyncio
async def test_register_and_login():
    test_email = f"test_auth_{uuid.uuid4()}@example.com"
    password = "securepassword123"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test Register
        response = await ac.post("/auth/register", json={"email": test_email, "password": password})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_email
        assert "id" in data
        
        # Test Duplicate Register
        response_dup = await ac.post("/auth/register", json={"email": test_email, "password": password})
        assert response_dup.status_code == 400
        
        # Test Login
        login_resp = await ac.post("/auth/login", data={"username": test_email, "password": password})
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Test Login Failure
        login_fail = await ac.post("/auth/login", data={"username": test_email, "password": "wrongpassword"})
        assert login_fail.status_code == 401
