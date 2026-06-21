from typing import AsyncIterator

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.models.message import Message, Role


class AIServiceError(Exception):
    pass

_client = genai.Client(api_key=settings.AI_API_KEY)

_ROLE_MAP = {
    Role.user: "user",
    Role.assistant: "model",
}


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

        "Language:\n"
        "- Always respond in the same language the user writes in.\n"
    )


def build_prompt(user_name: str, messages: list[Message]) -> list[types.Content]:
    return [
        types.Content(
            role=_ROLE_MAP[message.role],
            parts=[types.Part(text=message.content)],
        )
        for message in messages
    ]


async def stream_response(user_name: str, messages: list[Message]) -> AsyncIterator[str]:
    contents = build_prompt(user_name, messages)
    config = types.GenerateContentConfig(
        system_instruction=_system_prompt(user_name),
    )
    try:
        async for chunk in _client.aio.models.generate_content_stream(
            model=settings.AI_MODEL,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
    except APIError as e:
        raise AIServiceError(str(e)) from e
