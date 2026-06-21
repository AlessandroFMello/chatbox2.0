from datetime import datetime, timezone

import pytest

from app.models.conversation import ConversationOut
from app.models.message import Message


class InMemoryConversationRepository:
    def __init__(self):
        self._store: dict[str, ConversationOut] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return str(self._counter)

    async def get_by_email(self, email: str) -> ConversationOut | None:
        return next((c for c in self._store.values() if c.user_email == email), None)

    async def create(self, name: str, email: str) -> ConversationOut:
        now = datetime.now(timezone.utc)
        conversation = ConversationOut(
            id=self._next_id(),
            user_name=name,
            user_email=email,
            messages=[],
            created_at=now,
            updated_at=now,
        )
        self._store[conversation.id] = conversation
        return conversation

    async def get_by_id(self, conversation_id: str) -> ConversationOut | None:
        return self._store.get(conversation_id)

    async def append_message(self, conversation_id: str, message: Message) -> None:
        conversation = self._store[conversation_id]
        updated_messages = list(conversation.messages) + [message]
        self._store[conversation_id] = conversation.model_copy(
            update={"messages": updated_messages, "updated_at": datetime.now(timezone.utc)}
        )


@pytest.fixture
def repo() -> InMemoryConversationRepository:
    return InMemoryConversationRepository()
