import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    huawei_auth = Column(JSONB, nullable=True)

    activities = relationship("Activity", back_populates="user")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    mongo_ref_id = Column(String, nullable=True)
    source = Column(String, nullable=False)
    activity_type = Column(String, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=True)
    avg_heart_rate = Column(Integer, nullable=True)
    steps = Column(Integer, nullable=True)
    resting_heart_rate = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("ix_activities_user_id_start_time", "user_id", "start_time"),
    )
