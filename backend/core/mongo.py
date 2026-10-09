from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from datetime import datetime, timezone
from bson.objectid import ObjectId

client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=5000)
db = client.get_database("fitness")
raw_activities = db.get_collection("raw_activities")

async def insert_raw_activity(user_id: str, source: str, raw_input: str, extracted_json: str = None) -> str:
    doc = {
        "user_id": user_id,
        "source": source,
        "raw_input": raw_input,
        "extracted_json": extracted_json,
        "created_at": datetime.now(timezone.utc)
    }
    result = await raw_activities.insert_one(doc)
    return str(result.inserted_id)

async def get_raw_activity(doc_id: str):
    doc = await raw_activities.find_one({"_id": ObjectId(doc_id)})
    return doc

async def update_raw_activity_extracted(doc_id: str, extracted_json: str):
    await raw_activities.update_one(
        {"_id": ObjectId(doc_id)},
        {"$set": {"extracted_json": extracted_json}}
    )
