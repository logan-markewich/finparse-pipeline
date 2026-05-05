"""Thin LLM wrapper using litellm.

Attendees can swap providers by changing LLM_MODEL in .env
(e.g. "openai/gpt-4o", "anthropic/claude-sonnet-4-6").
"""

from litellm import acompletion

from app.config import settings


async def chat_completion(
    messages: list[dict],
    response_format: dict | None = None,
    temperature: float = 0.0,
) -> str:
    """Send a chat completion request and return the response content."""
    kwargs = {}
    if response_format is not None:
        kwargs["response_format"] = response_format

    response = await acompletion(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        **kwargs,
    )
    return response.choices[0].message.content
