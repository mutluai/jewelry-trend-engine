import logging
import time
import asyncio
from config import get_settings

logger = logging.getLogger(__name__)


def _get_gemini_model(model_name: str, system: str, expect_json: bool):
    import google.generativeai as genai
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    genai.configure(api_key=settings.gemini_api_key)

    generation_config = {"max_output_tokens": settings.ai_max_tokens}
    if expect_json:
        generation_config["response_mime_type"] = "application/json"

    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system,
        generation_config=generation_config,
    )


async def call_gemini(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    expect_json: bool = False,
) -> tuple[str, dict]:
    """Call Gemini API. Returns (content_text, usage_metadata)."""
    settings = get_settings()
    model_name = model or settings.ai_model
    system_prompt = system or "You are a jewelry market analyst. Respond only with valid JSON when asked."

    gemini_model = _get_gemini_model(model_name, system_prompt, expect_json)

    start = time.monotonic()
    try:
        response = await gemini_model.generate_content_async(prompt)
        latency_ms = int((time.monotonic() - start) * 1000)

        content = response.text or ""
        meta = response.usage_metadata
        usage = {
            "model": model_name,
            "input_tokens": meta.prompt_token_count if meta else 0,
            "output_tokens": meta.candidates_token_count if meta else 0,
            "latency_ms": latency_ms,
        }
        return content, usage

    except Exception as e:
        logger.error(f"Gemini API call failed: {e}", exc_info=True)
        raise


# Alias so existing code that imports call_claude still works
call_claude = call_gemini
