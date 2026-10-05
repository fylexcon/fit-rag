import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import User, Activity
from core.schemas import ActivityResponse
from core.auth import get_current_user
from openai import AsyncOpenAI
from core.config import settings
from datetime import datetime, timezone

router = APIRouter(prefix="/workouts", tags=["workouts"])

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

@router.post("/manual", response_model=ActivityResponse)
async def manual_workout(
    text: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Must provide text or image file")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if text:
        messages.append({"role": "user", "content": text})
    elif file:
        import base64
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        image_url = f"data:{file.content_type};base64,{base64_image}"
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
        raise HTTPException(status_code=500, detail=f"LLM extraction failed: {str(e)}")

    start_time = None
    if data.get("start_time"):
        try:
            start_time = datetime.fromisoformat(data.get("start_time").replace("Z", "+00:00"))
        except ValueError:
            pass
    if not start_time:
        start_time = datetime.now(timezone.utc)

    activity = Activity(
        user_id=current_user.id,
        source="manual",
        activity_type=data.get("activity_type", "unknown"),
        duration_minutes=float(data.get("duration_minutes", 0)),
        distance_km=float(data.get("distance_km")) if data.get("distance_km") is not None else None,
        avg_heart_rate=int(data.get("avg_heart_rate")) if data.get("avg_heart_rate") is not None else None,
        notes=data.get("notes"),
        start_time=start_time
    )
    
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    
    return activity
