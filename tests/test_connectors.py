"""Tests for connector layer — only mock connector tested (no API keys needed)."""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_mock_connector_fetch():
    from connectors.mock_demo import MockDemoConnector
    connector = MockDemoConnector(num_products=5)
    items = await connector.fetch()
    assert len(items) == 5
    for item in items:
        assert item.title
        assert item.price is not None
        assert item.raw_payload.get("is_mock") is True


@pytest.mark.asyncio
async def test_mock_connector_normalize():
    from connectors.mock_demo import MockDemoConnector
    connector = MockDemoConnector(num_products=1)
    raw_items = await connector.fetch()
    assert raw_items
    product = await connector.normalize(raw_items[0])
    assert product.title
    assert product.is_mock is True
    assert product.source_name == "mock_demo"
    assert product.price_tier in ("budget", "mid", "premium", "luxury")


@pytest.mark.asyncio
async def test_mock_connector_validate():
    from connectors.mock_demo import MockDemoConnector
    from connectors.base import ProductData
    from datetime import datetime, timezone

    connector = MockDemoConnector()
    valid = ProductData(title="Valid Product", is_mock=True, source_name="mock_demo",
                        collected_at=datetime.now(timezone.utc))
    invalid = ProductData(title="  ", is_mock=True, source_name="mock_demo",
                          collected_at=datetime.now(timezone.utc))
    assert connector.validate(valid) is True
    assert connector.validate(invalid) is False


def test_etsy_stub_mode():
    import os
    os.environ.pop("ETSY_API_KEY", None)
    from connectors.etsy import EtsyConnector
    # Re-import to pick up cleared env var
    connector = EtsyConnector.__new__(EtsyConnector)
    connector.name = "etsy"
    connector.is_stub = True
    items = connector._stub_data()
    assert len(items) > 0
    assert all(r.raw_payload.get("is_stub") for r in items)


def test_pinterest_stub_mode():
    from connectors.pinterest import PinterestConnector
    connector = PinterestConnector.__new__(PinterestConnector)
    connector.is_stub = True
    items = connector._stub_data()
    assert len(items) > 0
    assert all(r.raw_payload.get("is_stub") for r in items)


def test_base_price_tier():
    from connectors.base import BaseConnector

    class ConcreteConnector(BaseConnector):
        name = "test"
        async def fetch(self): return []
        async def normalize(self, raw): return None

    c = ConcreteConnector()
    assert c.infer_price_tier(20) == "budget"
    assert c.infer_price_tier(50) == "mid"
    assert c.infer_price_tier(100) == "premium"
    assert c.infer_price_tier(200) == "luxury"
    assert c.infer_price_tier(None) is None


def test_manual_upload_csv_parsing():
    from connectors.manual_upload import ManualUploadConnector
    connector = ManualUploadConnector()
    csv = "title,price,currency\nTest Ring,45.99,USD\nTest Necklace,65.00,USD"
    items = connector._parse_content(csv, "csv")
    assert len(items) == 2
    assert items[0].title == "Test Ring"
    assert items[0].price == 45.99


def test_manual_upload_json_parsing():
    import json
    from connectors.manual_upload import ManualUploadConnector
    connector = ManualUploadConnector()
    data = [
        {"title": "Ring A", "price": "35.00", "currency": "USD"},
        {"title": "Necklace B", "price": "55.00", "currency": "USD"},
    ]
    items = connector._parse_content(json.dumps(data), "json")
    assert len(items) == 2
    assert items[1].title == "Necklace B"
