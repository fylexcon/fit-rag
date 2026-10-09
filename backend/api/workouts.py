import base64
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.models import User
from core.auth import get_current_user
from core.mongo import insert_raw_activity
from tasks.workout_tasks import process_manual_workout_task

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("/manual", status_code=status.HTTP_202_ACCEPTED)
async def manual_workout(
    text: str = Form(None),
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not text and not file:
        raise HTTPException(status_code=400, detail="Must provide text or image file")

    if text:
        source = "manual_text"
        raw_input = text
    else:
        source = "manual_image"
        contents = await file.read()
        raw_input = base64.b64encode(contents).decode('utf-8')
        
    raw_doc_id = await insert_raw_activity(
        user_id=str(current_user.id),
        source=source,
        raw_input=raw_input
    )
    
    process_manual_workout_task.delay(raw_doc_id, str(current_user.id))
    
    return {"status": "processing", "raw_id": raw_doc_id}
