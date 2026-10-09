from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis
from core.config import settings
from api import auth, workouts, activities

app = FastAPI(title="Fitness AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(activities.router)

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "postgres": "down",
        "mongodb": "down",
        "redis": "down"
    }
    
    # Check Postgres
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            health_status["postgres"] = "up"
        await engine.dispose()
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["postgres"] = f"down: {str(e)}"

    # Check MongoDB
    try:
        client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000)
        await client.server_info()
        health_status["mongodb"] = "up"
        client.close()
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["mongodb"] = f"down: {str(e)}"
        
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        if await r.ping():
            health_status["redis"] = "up"
        await r.aclose()
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["redis"] = f"down: {str(e)}"
        
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
        
    return health_status
