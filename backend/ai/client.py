import logging
from functools import lru_cache
import anthropic
from config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_anthropic_client() -> anthropic.AsyncAnthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    return anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def call_claude(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    expect_json: bool = False,
) -> tuple[str, dict]:
    """
    Call Claude API and return (content_text, usage_metadata).
    usage_metadata = {model, input_tokens, output_tokens, latency_ms}
    """
    import time
    settings = get_settings()
    client = get_anthropic_client()

    model = model or settings.ai_model
    max_tokens = max_tokens or settings.ai_max_tokens

    system_prompt = system or "You are a jewelry market analyst. Respond only with valid JSON when asked."

    messages = [{"role": "user", "content": prompt}]

    start = time.monotonic()
    try:
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        content = response.content[0].text if response.content else ""
        usage = {
            "model": model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "latency_ms": latency_ms,
        }
        return content, usage

    except anthropic.RateLimitError:
        logger.warning("Anthropic rate limited — waiting 30s")
        import asyncio
        await asyncio.sleep(30)
        raise
    except Exception as e:
        logger.error(f"Claude API call failed: {e}", exc_info=True)
        raise
