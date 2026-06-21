from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.conversation import ConversationCreate, ConversationOut
from app.models.message import Message
from app.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


class MessageCreate(BaseModel):
    content: str


@router.post("", response_model=ConversationOut, status_code=201)
async def create_or_get_conversation(body: ConversationCreate) -> ConversationOut:
    return await conversation_service.get_or_create(body.name, body.email)


@router.get("/lookup", response_model=ConversationOut)
async def lookup_conversation(email: str) -> ConversationOut:
    conversation = await conversation_service.lookup_by_email(email)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(conversation_id: str) -> ConversationOut:
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/{conversation_id}/messages", response_model=Message, status_code=201)
async def add_message(conversation_id: str, body: MessageCreate) -> Message:
    return await conversation_service.add_user_message(conversation_id, body.content)


@router.delete("/{conversation_id}/messages", status_code=204)
async def clear_messages(conversation_id: str) -> None:
    conversation = await conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await conversation_service.clear_messages(conversation_id)
