import json
import asyncio
from core.celery_app import celery_app
from core.mongo import get_raw_activity, update_raw_activity_extracted
from core.database import AsyncSessionLocal
from core.models import Activity
from openai import AsyncOpenAI
from core.config import settings
from datetime import datetime, timezone

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """
Extract workout information from the provided text or image.
Respond ONLY with a JSON object matching this schema:
{
    "activity_type": "string (e.g. running, cycling, swimming, lifting)",
    "duration_minutes": "float (total duration in minutes)",
    "distance_km": "float or null (if applicable)",
    "avg_heart_rate": "int or null",
    "notes": "string or null (summary of the workout)",
    "start_time": "ISO8601 string (assume current time if not provided)"
}
"""

async def async_process_workout(raw_doc_id: str, user_id: str):
    raw_doc = await get_raw_activity(raw_doc_id)
    if not raw_doc:
        return
        
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if raw_doc["source"] == "manual_text":
        messages.append({"role": "user", "content": raw_doc["raw_input"]})
    else:
        image_url = f"data:image/jpeg;base64,{raw_doc['raw_input']}"
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract the workout data from this image."},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        })
        
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={ "type": "json_object" }
        )
        llm_output = response.choices[0].message.content
        data = json.loads(llm_output)
    except Exception as e:
        print(f"LLM extraction failed: {str(e)}")
        return

    await update_raw_activity_extracted(raw_doc_id, llm_output)

    start_time = None
    if data.get("start_time"):
        try:
            start_time = datetime.fromisoformat(data.get("start_time").replace("Z", "+00:00"))
        except ValueError:
            pass
    if not start_time:
        start_time = datetime.now(timezone.utc)

    import uuid
    async with AsyncSessionLocal() as db:
        activity = Activity(
            user_id=uuid.UUID(user_id),
            mongo_ref_id=raw_doc_id,
            source=raw_doc["source"],
            activity_type=data.get("activity_type", "unknown"),
            duration_minutes=float(data.get("duration_minutes", 0)),
            distance_km=float(data.get("distance_km")) if data.get("distance_km") is not None else None,
            avg_heart_rate=int(data.get("avg_heart_rate")) if data.get("avg_heart_rate") is not None else None,
            notes=data.get("notes"),
            start_time=start_time
        )
        db.add(activity)
        await db.commit()

@celery_app.task(name="tasks.process_manual_workout_task")
def process_manual_workout_task(raw_doc_id: str, user_id: str):
    asyncio.run(async_process_workout(raw_doc_id, user_id))
