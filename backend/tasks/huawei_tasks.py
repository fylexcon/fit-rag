import asyncio
import httpx
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.future import select
from core.database import AsyncSessionLocal
from core.models import User, Activity
from core.mongo import insert_raw_activity
from core.huawei import refresh_huawei_token_if_needed
import json

HUAWEI_HEALTH_API_URL = "https://health-api.cloud.huawei.com/healthkit/v1/activityRecords"

async def async_poll_huawei_health():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.huawei_auth.is_not(None)))
        users = result.scalars().all()

        for user in users:
            try:
                access_token = await refresh_huawei_token_if_needed(user, db)
                if not access_token:
                    continue
                
                # We can store last_synced_at in huawei_auth JSONB
                last_synced_at = user.huawei_auth.get("last_synced_at", 0)
                current_time = int(datetime.now(timezone.utc).timestamp())

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        HUAWEI_HEALTH_API_URL,
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"startTime": last_synced_at, "endTime": current_time}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        records = data.get("activityRecords", [])
                        
                        for record in records:
                            # Store raw payload in MongoDB
                            raw_doc_id = await insert_raw_activity(
                                user_id=str(user.id),
                                source="huawei",
                                raw_input=json.dumps(record)
                            )
                            
                            # Parse normalized row
                            activity_type = record.get("activityType", "unknown")
                            duration_minutes = record.get("duration", 0) / 60.0
                            distance_km = record.get("distance", 0) / 1000.0 if "distance" in record else None
                            avg_heart_rate = record.get("avgHeartRate")
                            
                            # We expect 'startTime' in ms or similar from Huawei, but for simplicity:
                            start_time_val = record.get("startTime", current_time * 1000)
                            start_time = datetime.fromtimestamp(start_time_val / 1000, tz=timezone.utc)
                            
                            activity = Activity(
                                user_id=user.id,
                                mongo_ref_id=str(raw_doc_id),
                                source="huawei",
                                activity_type=activity_type,
                                duration_minutes=float(duration_minutes),
                                distance_km=float(distance_km) if distance_km is not None else None,
                                avg_heart_rate=int(avg_heart_rate) if avg_heart_rate is not None else None,
                                start_time=start_time
                            )
                            db.add(activity)

                        # Update last_synced_at
                        auth_data = dict(user.huawei_auth)
                        auth_data["last_synced_at"] = current_time
                        user.huawei_auth = auth_data
                        db.add(user)
                        
                        await db.commit()
            except Exception as e:
                print(f"Error polling user {user.id}: {e}")
                await db.rollback()

@shared_task
def poll_huawei_health():
    asyncio.run(async_poll_huawei_health())
