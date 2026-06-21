from app.models.conversation import ConversationOut
from app.models.message import Message, Role
from app.repositories import conversation_repository


async def get_or_create(name: str, email: str) -> ConversationOut:
    existing = await conversation_repository.get_by_email(email)
    if existing:
        return existing
    return await conversation_repository.create(name, email)


async def add_user_message(conversation_id: str, content: str) -> Message:
    message = Message(role=Role.user, content=content)
    await conversation_repository.append_message(conversation_id, message)
    return message


async def get_conversation(conversation_id: str) -> ConversationOut | None:
    return await conversation_repository.get_by_id(conversation_id)


async def persist_ai_message(conversation_id: str, content: str) -> None:
    message = Message(role=Role.assistant, content=content)
    await conversation_repository.append_message(conversation_id, message)
