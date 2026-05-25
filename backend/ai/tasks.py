"""
AI Task Functions — All AI operations in the Jewelry Trend Engine.
Uses Anthropic Claude API exclusively.
Every call logs: model, tokens, latency, timestamp.
"""
import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from .client import call_claude
from .structured_outputs import (
    extract_json, ProductAttributes, TrendPattern, OpportunityAnalysis, VisualAnalysis
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning(f"Prompt file not found: {path}")
    return ""


async def extract_product_attributes(
    title: str,
    description: str | None = None,
) -> tuple[ProductAttributes, dict]:
    """
    Extract structured jewelry attributes from product title + description.
    Returns (ProductAttributes, usage_metadata).
    """
    prompt_template = _load_prompt("product_extractor.md")
    if not prompt_template:
        prompt_template = """Analyze this jewelry product and extract attributes as JSON:

Title: {title}
Description: {description}

Return JSON with fields: material, stone, style, category, color, target_gender, price_tier, theme, style_tags (list), confidence (0-1)"""

    prompt = prompt_template.format(
        title=title,
        description=description or "No description provided",
    )

    try:
        content, usage = await call_claude(prompt, expect_json=True)
        data = extract_json(content)
        if data and isinstance(data, dict):
            attrs = ProductAttributes(**{k: v for k, v in data.items() if k in ProductAttributes.model_fields})
            return attrs, usage
    except Exception as e:
        logger.error(f"extract_product_attributes failed: {e}")

    return ProductAttributes(), {}


async def analyze_image(image_url: str) -> tuple[VisualAnalysis, dict]:
    """
    Analyze product image using Claude vision.
    Returns (VisualAnalysis, usage_metadata).
    """
    from config import get_settings
    settings = get_settings()

    prompt_template = _load_prompt("image_analyzer.md")
    if not prompt_template:
        prompt_template = "Analyze this jewelry product image. Return JSON with: visual_tags, style_description, material_guess, design_complexity, similar_styles."

    try:
        import anthropic
        client_module = __import__("ai.client", fromlist=["get_anthropic_client"])
        client = client_module.get_anthropic_client()

        import time
        start = time.monotonic()
        response = await client.messages.create(
            model=settings.ai_model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "url", "url": image_url}},
                    {"type": "text", "text": prompt_template},
                ],
            }],
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        content = response.content[0].text
        usage = {
            "model": settings.ai_model,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "latency_ms": latency_ms,
        }

        data = extract_json(content)
        if data and isinstance(data, dict):
            analysis = VisualAnalysis(**{k: v for k, v in data.items() if k in VisualAnalysis.model_fields})
            return analysis, usage

    except Exception as e:
        logger.error(f"analyze_image failed for {image_url}: {e}")

    return VisualAnalysis(), {}


async def detect_trend_patterns(
    products: list[dict],
    period_days: int = 7,
) -> tuple[list[TrendPattern], dict]:
    """
    Detect emerging patterns from a batch of recent products.
    products: list of dicts with title, description, category, material, style fields.
    """
    prompt_template = _load_prompt("trend_detector.md")

    product_summary = "\n".join([
        f"- {p.get('title', 'Unknown')}: {p.get('category', '')} | {p.get('material', '')} | {p.get('theme', '')}"
        for p in products[:50]
    ])

    if not prompt_template:
        prompt_template = """You are a jewelry market trend analyst.

Analyze these {count} jewelry products collected in the last {days} days and identify emerging trends:

{products}

Return a JSON array of trend patterns. Each pattern has:
- pattern_type: string (material_trend, style_trend, category_trend, theme_trend)
- description: string (what is trending)
- keywords: list of relevant keywords
- materials: list of materials involved
- styles: list of styles involved
- direction: "rising" | "declining" | "stable"
- confidence: float 0-1
- evidence_count: int (how many products support this)"""

    prompt = prompt_template.format(
        count=len(products),
        days=period_days,
        products=product_summary,
    )

    try:
        content, usage = await call_claude(prompt, expect_json=True, max_tokens=2048)
        data = extract_json(content)
        if data and isinstance(data, list):
            patterns = [
                TrendPattern(**{k: v for k, v in p.items() if k in TrendPattern.model_fields})
                for p in data
                if isinstance(p, dict)
            ]
            return patterns, usage
    except Exception as e:
        logger.error(f"detect_trend_patterns failed: {e}")

    return [], {}


async def score_opportunity_ai(
    product: dict,
    brand_profile: dict,
    score_components: dict,
) -> tuple[OpportunityAnalysis, dict]:
    """
    Generate AI narrative and recommendation for a scored product opportunity.
    """
    prompt_template = _load_prompt("opportunity_scorer.md")

    if not prompt_template:
        prompt_template = """You are a jewelry business consultant for a brand in {market} market.

Product: {title}
Category: {category}
Material: {material}
Price: {price} USD
Score breakdown:
- Trend velocity: {trend_velocity}/100
- Cross-source validation: {cross_source}/100
- Competition density (inverted): {competition_density}/100
- Novelty: {novelty}/100
- Brand fit: {brand_fit}/100
- Review signals: {review_signal}/100
Total score: {total_score}/100

Brand focus: {style_focus}
Target customer: {target_customer}

Return JSON with:
- narrative: (2-3 sentences why this is an opportunity)
- recommendation: (specific action — design, restock, test, promote)
- risk_notes: (what could go wrong)
- score_explanation: (dict with brief reason per component)"""

    prompt = prompt_template.format(
        title=product.get("title", ""),
        category=product.get("category", ""),
        material=product.get("material", ""),
        price=product.get("price_usd", "unknown"),
        total_score=score_components.get("total_score", 0),
        trend_velocity=score_components.get("trend_velocity", 0),
        cross_source=score_components.get("cross_source", 0),
        competition_density=score_components.get("competition_density", 0),
        novelty=score_components.get("novelty", 0),
        brand_fit=score_components.get("brand_fit", 0),
        review_signal=score_components.get("review_signal", 0),
        market=brand_profile.get("market", "Turkey"),
        style_focus=brand_profile.get("style_focus", "minimalist"),
        target_customer=brand_profile.get("target_customer", "women 20-40"),
    )

    try:
        content, usage = await call_claude(prompt, expect_json=True)
        data = extract_json(content)
        if data and isinstance(data, dict):
            analysis = OpportunityAnalysis(
                narrative=data.get("narrative", ""),
                recommendation=data.get("recommendation", ""),
                risk_notes=data.get("risk_notes", ""),
                score_explanation=data.get("score_explanation", {}),
            )
            return analysis, usage
    except Exception as e:
        logger.error(f"score_opportunity_ai failed: {e}")

    return OpportunityAnalysis(narrative="", recommendation="", risk_notes=""), {}


async def generate_report(
    report_type: str,
    data_summary: dict,
    language: str = "tr",
) -> tuple[str, dict]:
    """
    Generate a full report in Turkish (default) or English.
    Returns (markdown_text, usage_metadata).
    """
    prompt_template = _load_prompt("report_generator_tr.md")

    if not prompt_template:
        prompt_template = """Sen bir mücevher markası için pazar araştırması yapan bir analistsin.

Rapor türü: {report_type}
Dönem: {period}

Veriler:
- Toplam ürün: {total_products}
- Yeni sinyaller: {new_signals}
- En yüksek puanlı fırsat: {top_opportunity}
- Yükselen materyaller: {rising_materials}
- Yükselen stiller: {rising_styles}

Lütfen Türkçe, profesyonel bir {report_type} raporu yaz.
Markdown formatında, başlıklar ve maddeler kullanarak.
Sonunda somut öneriler ver."""

    prompt = prompt_template.format(
        report_type=report_type,
        period=data_summary.get("period", "Son 7 gün"),
        total_products=data_summary.get("total_products", 0),
        new_signals=data_summary.get("new_signals", 0),
        top_opportunity=data_summary.get("top_opportunity", "N/A"),
        rising_materials=", ".join(data_summary.get("rising_materials", [])),
        rising_styles=", ".join(data_summary.get("rising_styles", [])),
    )

    try:
        content, usage = await call_claude(
            prompt,
            system="Sen bir mücevher pazar analisti ve iş danışmanısın. Türkçe, akıcı ve profesyonel raporlar yazıyorsun.",
            max_tokens=4000,
            expect_json=False,
        )
        return content, usage
    except Exception as e:
        logger.error(f"generate_report failed: {e}")
        return f"# Rapor Oluşturulamadı\n\nHata: {e}", {}


async def analyze_competitors(
    competitor_products: list[dict],
    brand_profile: dict,
) -> tuple[dict, dict]:
    """
    Analyze competitor product batch for positioning, gaps, threats.
    """
    prompt_template = _load_prompt("competitor_analyzer.md")

    products_text = "\n".join([
        f"- {p.get('title', '')}: ${p.get('price_usd', '?')} | {p.get('category', '')} | {p.get('material', '')}"
        for p in competitor_products[:30]
    ])

    if not prompt_template:
        prompt_template = """Analyze these competitor jewelry products:

{products}

Brand profile: {style_focus}, price range ${price_min}-${price_max}, market: {market}

Return JSON with:
- positioning: (how competitor is positioned vs our brand)
- gaps: list of product gaps we could fill
- threats: list of competitive threats
- opportunities: list of opportunities their catalog reveals
- price_analysis: (their price positioning)"""

    prompt = prompt_template.format(
        products=products_text,
        style_focus=brand_profile.get("style_focus", "minimalist"),
        price_min=brand_profile.get("price_min", 25),
        price_max=brand_profile.get("price_max", 250),
        market=brand_profile.get("market", "Turkey"),
    )

    try:
        content, usage = await call_claude(prompt, expect_json=True, max_tokens=2048)
        data = extract_json(content)
        if data and isinstance(data, dict):
            return data, usage
    except Exception as e:
        logger.error(f"analyze_competitors failed: {e}")

    return {}, {}
