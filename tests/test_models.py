"""Tests for SQLAlchemy models."""
import pytest
import pytest_asyncio
import uuid
from sqlalchemy import select


@pytest.mark.asyncio
async def test_create_product(db):
    from models.product import Product
    product = Product(
        title="Test Gold Ring",
        price=45.99,
        currency="USD",
        price_usd=45.99,
        review_count=50,
        is_mock=True,
        status="raw",
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)

    assert product.id is not None
    assert product.title == "Test Gold Ring"
    assert product.is_mock is True
    assert product.status == "raw"


@pytest.mark.asyncio
async def test_create_opportunity_score(db):
    from models.product import Product
    from models.scoring import OpportunityScore

    product = Product(title="Score Test Product", is_mock=True, status="raw")
    db.add(product)
    await db.flush()

    score = OpportunityScore(
        product_id=product.id,
        total_score=72.5,
        trend_velocity_score=80.0,
        cross_source_score=60.0,
        novelty_score=70.0,
        brand_fit_score=75.0,
        review_signal_score=65.0,
        competition_density_score=75.0,
        score_version="1.0",
    )
    db.add(score)
    await db.commit()
    await db.refresh(score)

    assert score.total_score == 72.5
    assert score.product_id == product.id


@pytest.mark.asyncio
async def test_create_trend_signal(db):
    from models.trend import TrendSignal

    signal = TrendSignal(
        signal_type="keyword_trend",
        keyword="minimalist gold ring",
        trend_direction="rising",
        velocity_score=45.0,
        interest_value=78.0,
        geo="TR",
        source_name="google_trends",
        is_mock=True,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    assert signal.keyword == "minimalist gold ring"
    assert signal.trend_direction == "rising"
    assert signal.is_mock is True


@pytest.mark.asyncio
async def test_create_source(db):
    from models.source import Source

    source = Source(
        name="test_connector",
        display_name="Test Connector",
        connector_class="connectors.mock_demo.MockDemoConnector",
        legal_status="mock",
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    assert source.name == "test_connector"
    assert source.legal_status == "mock"
