# Connector Documentation

## Overview

Each connector extends `BaseConnector` and implements the same interface:
- `fetch()` → raw data from source
- `normalize()` → standard ProductData
- `validate()` → completeness check
- `save()` → store to database
- `run()` → complete pipeline

## Connector Status

| Connector | Status | Requires | Legal |
|-----------|--------|----------|-------|
| mock_demo | ✅ Ready | Nothing | Mock |
| google_trends | ✅ Ready | Nothing (unofficial) | Public |
| etsy | ✅ Ready (stub fallback) | `ETSY_API_KEY` | Official API |
| pinterest | ⚠️ Stub | `PINTEREST_ACCESS_TOKEN` | Stub |
| manual_upload | ✅ Ready | Supabase Storage | User-provided |
| web_compliant | ✅ Ready | Target URLs in config | Public (robots.txt) |

## mock_demo

Generates 30 realistic synthetic jewelry products. Works with zero configuration.

```python
from connectors.mock_demo import MockDemoConnector
connector = MockDemoConnector(num_products=50)
result = await connector.run()
```

## google_trends

Uses pytrends to fetch keyword interest data for 20 jewelry keywords across TR, DE, GB.

**Rate limit:** 60 seconds between batches (to avoid Google rate limiting).

```python
from connectors.google_trends import GoogleTrendsConnector
connector = GoogleTrendsConnector()
result = await connector.run()
```

## etsy

Uses Etsy Open API v3. Falls back to stub data if `ETSY_API_KEY` is not set.

**Get API key:** Register at [etsy.com/developers](https://www.etsy.com/developers/)

```python
# Set ETSY_API_KEY in .env first
from connectors.etsy import EtsyConnector
connector = EtsyConnector()  # auto-detects stub mode
result = await connector.run()
```

## pinterest

Stub connector. Returns mock Pinterest-style data until API access is approved.

**Get API access:** Apply at [developers.pinterest.com](https://developers.pinterest.com/)

## manual_upload

Processes CSV or JSON files from Supabase Storage.

**CSV format:**
```
title,description,price,currency,source_url,image_url,review_count
Gold Ring,Description,45.99,USD,https://...,https://...,150
```

**JSON format:**
```json
[{"title": "Gold Ring", "price": 45.99, "currency": "USD"}]
```

## web_compliant

Scrapes product pages that allow it per robots.txt. Requires target URLs in config.

**Always checks robots.txt before fetching.** Never bypasses authentication.

```python
urls = ["https://example.com/product/123"]  # must pass robots.txt check
from connectors.web_compliant import WebCompliantConnector
connector = WebCompliantConnector(urls=urls)
result = await connector.run()
```
