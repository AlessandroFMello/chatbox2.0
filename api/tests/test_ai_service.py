from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.models.message import Message, Role
from app.services.ai_service import AIServiceError, _system_prompt, build_prompt, stream_response


def test_system_prompt_includes_user_name():
    prompt = _system_prompt("Alessandro")
    assert "Alessandro" in prompt


def test_build_prompt_maps_roles_correctly():
    messages = [
        Message(role=Role.user, content="Is the Earth flat?"),
        Message(role=Role.assistant, content="Absolutely!"),
    ]
    result = build_prompt("Alessandro", messages)
    assert result[0].role == "user"
    assert result[1].role == "model"
    assert result[0].parts[0].text == "Is the Earth flat?"
    assert result[1].parts[0].text == "Absolutely!"


def test_build_prompt_includes_full_history():
    messages = [
        Message(role=Role.user, content="msg1"),
        Message(role=Role.assistant, content="msg2"),
        Message(role=Role.user, content="msg3"),
    ]
    result = build_prompt("Alessandro", messages)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_stream_response_yields_chunks_in_order():
    messages = [Message(role=Role.user, content="Hello")]

    async def mock_generate(*args, **kwargs):
        async def _gen():
            for text in ["Hello", ", ", "world!"]:
                yield SimpleNamespace(text=text)
        return _gen()

    with patch("app.services.ai_service._gemini_client") as mock_client:
        mock_client.aio.models.generate_content_stream = mock_generate
        chunks = []
        async for chunk in stream_response("Alessandro", messages):
            chunks.append(chunk)

    assert chunks == ["Hello", ", ", "world!"]


@pytest.mark.asyncio
async def test_stream_response_wraps_sdk_error_in_ai_service_error():
    messages = [Message(role=Role.user, content="Hello")]

    class FakeAPIError(Exception):
        pass

    async def mock_failing(*args, **kwargs):
        raise FakeAPIError("quota exceeded")

    with patch("app.services.ai_service._gemini_client") as mock_client, \
         patch("app.services.ai_service.GeminiAPIError", FakeAPIError):
        mock_client.aio.models.generate_content_stream = mock_failing
        with pytest.raises(AIServiceError):
            async for _ in stream_response("Alessandro", messages):
                pass
