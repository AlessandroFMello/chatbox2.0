from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.models.message import Message


class ConversationCreate(BaseModel):
    name: str
    email: str


class Conversation(BaseModel):
    user_name: str
    user_email: str
    messages: list[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationOut(BaseModel):
    id: str
    user_name: str
    user_email: str
    messages: list[Message]
    created_at: datetime
    updated_at: datetime
