"""Tests for the scoring engine."""
import pytest
from dataclasses import asdict


def test_score_weights_normalize():
    from services.scoring import ScoreWeights
    weights = ScoreWeights(
        trend_velocity=0.5,
        cross_source=0.5,
        competition_density=0.0,
        novelty=0.0,
        brand_fit=0.0,
        review_signal=0.0,
    )
    normalized = weights.normalize()
    total = (
        normalized.trend_velocity + normalized.cross_source
        + normalized.competition_density + normalized.novelty
        + normalized.brand_fit + normalized.review_signal
    )
    assert abs(total - 1.0) < 0.001


def test_score_basic_product():
    from services.scoring import ScoringEngine, ScoreWeights

    engine = ScoringEngine()
    product = {
        "title": "Minimalist Gold Ring",
        "category": "rings",
        "style": "minimalist",
        "material": "gold-plated",
        "review_count": 500,
        "review_rating": 4.7,
        "price_usd": 55.0,
    }
    context = {
        "brand_categories": ["rings", "necklaces"],
        "brand_styles": ["minimalist", "dainty"],
        "source_count": 2,
        "similar_product_count": 3,
        "days_since_first_seen": 5,
        "trend_velocity": 40,
    }
    total, components = engine.score_product(product, context)

    assert 0 <= total <= 100
    assert 0 <= components.brand_fit <= 100
    assert 0 <= components.review_signal <= 100


def test_high_review_count_boosts_score():
    from services.scoring import ScoringEngine

    engine = ScoringEngine()
    product_low = {"review_count": 5, "review_rating": 4.5}
    product_high = {"review_count": 2000, "review_rating": 4.5}

    _, comp_low = engine.score_product(product_low, {})
    _, comp_high = engine.score_product(product_high, {})

    assert comp_high.review_signal > comp_low.review_signal


def test_brand_fit_boost_for_matching_category():
    from services.scoring import ScoringEngine

    engine = ScoringEngine()
    product_match = {"category": "rings", "style": "minimalist"}
    product_miss = {"category": "watches", "style": "sporty"}
    context = {
        "brand_categories": ["rings", "necklaces"],
        "brand_styles": ["minimalist", "dainty"],
    }
    _, comp_match = engine.score_product(product_match, context)
    _, comp_miss = engine.score_product(product_miss, context)

    assert comp_match.brand_fit > comp_miss.brand_fit


def test_score_always_0_to_100():
    from services.scoring import ScoringEngine

    engine = ScoringEngine()
    # Extreme inputs
    product = {"review_count": 999999, "review_rating": 5.0}
    context = {"trend_velocity": 999, "source_count": 100}
    total, _ = engine.score_product(product, context)

    assert 0 <= total <= 100


def test_novelty_decreases_over_time():
    from services.scoring import ScoringEngine

    engine = ScoringEngine()
    product = {}
    new_context = {"days_since_first_seen": 2}
    old_context = {"days_since_first_seen": 180}

    _, comp_new = engine.score_product(product, new_context)
    _, comp_old = engine.score_product(product, old_context)

    assert comp_new.novelty > comp_old.novelty
