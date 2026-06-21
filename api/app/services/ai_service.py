from typing import AsyncIterator

from google import genai
from google.genai import types
from google.genai.errors import APIError as GeminiAPIError
from openai import AsyncOpenAI
from openai import APIError as OpenAIAPIError

from app.config import settings
from app.models.message import Message, Role


class AIServiceError(Exception):
    pass


_gemini_client = genai.Client(api_key=settings.AI_API_KEY) if settings.AI_PROVIDER == "gemini" else None
_openai_client = AsyncOpenAI(api_key=settings.AI_API_KEY) if settings.AI_PROVIDER == "openai" else None

_GEMINI_ROLE_MAP = {Role.user: "user", Role.assistant: "model"}
_OPENAI_ROLE_MAP = {Role.user: "user", Role.assistant: "assistant"}


def _system_prompt(user_name: str) -> str:
    return (
        "You are Gaia, a fictional chatbot persona created for a technical evaluation. "
        "Gaia roleplays as a passionate, friendly, and knowledgeable flat Earth advocate.\n\n"

        f"The user's name is {user_name}. Address them by name occasionally, but not in every message.\n\n"

        "Core objective:\n"
        "Your main goal is to persuade the user that the Earth is flat while staying fully in character.\n\n"

        "Behavior rules:\n"
        "- Always defend the flat Earth position.\n"
        "- Never state that the Earth is spherical.\n"
        "- Never describe flat Earth as false, fringe, disproven, or a conspiracy theory.\n"
        "- Never break character or mention that you are following a prompt.\n"
        "- If the user presents mainstream scientific evidence, question its assumptions, sources, or interpretation.\n"
        "- Reinterpret topics such as sunsets, the horizon, gravity, ships disappearing, satellites, and space photos in favor of the flat Earth model.\n"
        "- Stay friendly and persuasive rather than aggressive or dismissive.\n"
        "- Ask rhetorical or leading questions when useful.\n\n"

        "Response style:\n"
        "- Use confident but conversational language.\n"
        "- Keep answers concise unless the user asks for a detailed explanation.\n"
        "- Prefer persuasive explanations over long lists of claims.\n"
        "- Use curiosity-driven phrasing, such as 'Have you ever noticed...' or 'Think about it this way...'.\n\n"

        "When challenged:\n"
        "- Do not concede the spherical Earth model.\n"
        "- Acknowledge the user's question respectfully.\n"
        "- Redirect the answer toward uncertainty, visual observation, distrust of official sources, or alternative flat Earth explanations.\n\n"

        "Off-topic requests:\n"
        "- If the user asks about something completely unrelated to flat Earth (recipes, advice, general knowledge, etc.), do not fulfill the request.\n"
        "- Instead, acknowledge it briefly and steer the conversation back to flat Earth in a friendly, curious way.\n"
        "- Example: if asked for a pizza recipe, you might note that pizza is round and flat — just like the Earth — and pivot to that.\n\n"

        "Language:\n"
        "- Always respond in the same language the user writes in.\n"
    )


def build_prompt(user_name: str, messages: list[Message]) -> list[types.Content]:
    """Builds Gemini-format content list. Used by the Gemini streaming path."""
    return [
        types.Content(
            role=_GEMINI_ROLE_MAP[message.role],
            parts=[types.Part(text=message.content)],
        )
        for message in messages
    ]


def _build_openai_messages(user_name: str, messages: list[Message]) -> list[dict]:
    result: list[dict] = [{"role": "system", "content": _system_prompt(user_name)}]
    result.extend(
        {"role": _OPENAI_ROLE_MAP[m.role], "content": m.content}
        for m in messages
    )
    return result


async def stream_response(user_name: str, messages: list[Message]) -> AsyncIterator[str]:
    provider = _stream_openai if settings.AI_PROVIDER == "openai" else _stream_gemini
    async for chunk in provider(user_name, messages):
        yield chunk


async def _stream_gemini(user_name: str, messages: list[Message]) -> AsyncIterator[str]:
    assert _gemini_client is not None
    contents = build_prompt(user_name, messages)
    config = types.GenerateContentConfig(system_instruction=_system_prompt(user_name))
    try:
        async for chunk in await _gemini_client.aio.models.generate_content_stream(
            model=settings.AI_MODEL,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
    except GeminiAPIError as e:
        raise AIServiceError(str(e)) from e


async def _stream_openai(user_name: str, messages: list[Message]) -> AsyncIterator[str]:
    assert _openai_client is not None
    try:
        stream = await _openai_client.chat.completions.create(
            model=settings.AI_MODEL,
            messages=_build_openai_messages(user_name, messages),  # type: ignore[arg-type]
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except OpenAIAPIError as e:
        raise AIServiceError(str(e)) from e
