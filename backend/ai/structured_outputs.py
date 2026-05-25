import json
import re
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict | list | None:
    """Extract JSON from Claude response text, handling markdown code blocks."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Extract from markdown code block
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"\{.*\}",
        r"\[.*\]",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1) if "```" in pattern else match.group(0))
            except json.JSONDecodeError:
                continue

    logger.warning(f"Could not extract JSON from response: {text[:200]}")
    return None


class ProductAttributes(BaseModel):
    material: str | None = None
    stone: str | None = None
    style: str | None = None
    category: str | None = None
    color: str | None = None
    target_gender: str = "women"
    price_tier: str | None = None
    theme: str | None = None
    style_tags: list[str] = []
    confidence: float = 0.8


class TrendPattern(BaseModel):
    pattern_type: str
    description: str
    keywords: list[str] = []
    materials: list[str] = []
    styles: list[str] = []
    direction: str = "rising"
    confidence: float = 0.7
    evidence_count: int = 0


class OpportunityAnalysis(BaseModel):
    narrative: str
    recommendation: str
    risk_notes: str
    score_explanation: dict = {}


class VisualAnalysis(BaseModel):
    visual_tags: list[str] = []
    style_description: str | None = None
    material_guess: str | None = None
    design_complexity: str | None = None
    similar_styles: list[str] = []
