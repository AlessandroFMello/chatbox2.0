from datetime import datetime, timezone

from bson import ObjectId

from app.database import get_conversations_collection
from app.models.conversation import Conversation, ConversationOut
from app.models.message import Message


def _doc_to_out(doc: dict) -> ConversationOut:
    return ConversationOut(
        id=str(doc["_id"]),
        user_name=doc["user_name"],
        user_email=doc["user_email"],
        messages=[Message(**m) for m in doc.get("messages", [])],
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def get_by_email(email: str) -> ConversationOut | None:
    col = get_conversations_collection()
    doc = await col.find_one({"user_email": email})
    return _doc_to_out(doc) if doc else None


async def create(name: str, email: str) -> ConversationOut:
    col = get_conversations_collection()
    conversation = Conversation(user_name=name, user_email=email)
    result = await col.insert_one(conversation.model_dump())
    doc = await col.find_one({"_id": result.inserted_id})
    return _doc_to_out(doc)


async def get_by_id(conversation_id: str) -> ConversationOut | None:
    col = get_conversations_collection()
    doc = await col.find_one({"_id": ObjectId(conversation_id)})
    return _doc_to_out(doc) if doc else None


async def append_message(conversation_id: str, message: Message) -> None:
    col = get_conversations_collection()
    now = datetime.now(timezone.utc)
    await col.update_one(
        {"_id": ObjectId(conversation_id)},
        {
            "$push": {"messages": message.model_dump()},
            "$set": {"updated_at": now},
        },
    )


async def clear_messages(conversation_id: str) -> None:
    col = get_conversations_collection()
    now = datetime.now(timezone.utc)
    await col.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$set": {"messages": [], "updated_at": now}},
    )
