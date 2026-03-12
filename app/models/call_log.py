from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CallLog(SQLModel, table=True):
    __tablename__ = "call_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id", index=True)
    twilio_call_sid: Optional[str] = Field(default=None, max_length=64, unique=True)
    caller_number: str = Field(max_length=20)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[int] = Field(default=None)
    conversation_summary: Optional[str] = Field(default=None)
    caller_name: Optional[str] = Field(default=None, max_length=255)
    caller_inquiry: Optional[str] = Field(default=None)
    status: str = Field(default="in_progress", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
