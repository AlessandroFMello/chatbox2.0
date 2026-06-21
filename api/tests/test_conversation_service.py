from unittest.mock import patch

import pytest

from app.models.message import Role
from app.services import conversation_service


@pytest.mark.asyncio
async def test_get_or_create_creates_new_conversation(repo):
    with patch("app.services.conversation_service.conversation_repository", repo):
        result = await conversation_service.get_or_create("Alice", "alice@test.com")

    assert result.user_name == "Alice"
    assert result.user_email == "alice@test.com"
    assert result.messages == []


@pytest.mark.asyncio
async def test_get_or_create_returns_existing_on_duplicate_email(repo):
    with patch("app.services.conversation_service.conversation_repository", repo):
        first = await conversation_service.get_or_create("Alice", "alice@test.com")
        second = await conversation_service.get_or_create("Alice Updated", "alice@test.com")

    assert first.id == second.id


@pytest.mark.asyncio
async def test_add_user_message_appends_correctly(repo):
    with patch("app.services.conversation_service.conversation_repository", repo):
        conversation = await conversation_service.get_or_create("Alice", "alice@test.com")
        message = await conversation_service.add_user_message(conversation.id, "Hello!")
        updated = await repo.get_by_id(conversation.id)

    assert message.role == Role.user
    assert message.content == "Hello!"
    assert len(updated.messages) == 1
    assert updated.messages[0].content == "Hello!"


@pytest.mark.asyncio
async def test_persist_ai_message_appends_with_assistant_role(repo):
    with patch("app.services.conversation_service.conversation_repository", repo):
        conversation = await conversation_service.get_or_create("Alice", "alice@test.com")
        await conversation_service.persist_ai_message(conversation.id, "The Earth is flat!")
        updated = await repo.get_by_id(conversation.id)

    assert len(updated.messages) == 1
    assert updated.messages[0].role == Role.assistant
    assert updated.messages[0].content == "The Earth is flat!"
