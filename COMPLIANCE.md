# Compliance & Legal Documentation — Jewelry Trend Engine

**Version:** 1.0  
**Date:** 2026-05-25

---

## Overview

This document describes the legal and ethical framework for data collection in the Jewelry Trend Engine. Every data source connector has an explicit legal classification and operating constraint.

---

## Connector Legal Classification

| Connector | Legal Status | Mechanism | Notes |
|-----------|-------------|-----------|-------|
| Google Trends | ✅ Public Allowed | pytrends (unofficial wrapper of public UI) | Rate limited; no auth bypass |
| Etsy | ✅ Official API | Etsy Open API v3 | Requires registered API key |
| Pinterest | ✅ Official API | Pinterest API v5 | Requires Business account |
| Manual Upload | ✅ User-Provided | CSV/JSON via Supabase Storage | User is responsible for data legality |
| Web Compliant | ⚠️ Conditional | httpx + BeautifulSoup | Must pass robots.txt check per domain |
| Mock/Demo | ✅ Internal | Synthetic data generator | No external requests |

---

## robots.txt Compliance

The `web_compliant.py` connector implements mandatory robots.txt checking:

```python
# Before EVERY request to a new domain:
1. Fetch and parse robots.txt
2. Check if our user-agent is allowed to access the path
3. Respect Crawl-delay directive
4. If disallowed: log the block, skip the URL, never retry
5. Cache robots.txt for 24 hours to avoid repeated fetches
```

**User-Agent string used:** `JewelryTrendEngine/1.0 (+https://github.com/mutluai/jewelry-trend-engine; research-bot)`

---

## Rate Limiting Policy

| Connector | Minimum Delay | Max Requests/Hour |
|-----------|--------------|-------------------|
| Google Trends | 60 seconds between keyword batches | 10 |
| Etsy API | 1 second between requests | 500 (API limit) |
| Pinterest API | 1 second between requests | Per API quota |
| Web Compliant | 3 seconds between requests per domain | 20/domain |
| Mock/Demo | No limit | Unlimited |

---

## Data Retention Policy

| Data Type | Retention Period | Rationale |
|-----------|-----------------|-----------|
| Raw product snapshots | 12 months | Trend analysis requires historical data |
| AI analysis results | 12 months | Audit trail and quality improvement |
| Source run logs | 6 months | Debugging and compliance audit |
| Generated reports | 24 months | Business record keeping |
| Error logs | 3 months | Operational debugging |

---

## What We Do NOT Do

The following activities are explicitly prohibited in this system:

- ❌ Bypassing CAPTCHAs or bot-detection systems
- ❌ Logging in to any service using credentials we don't own
- ❌ Accessing any content behind authentication walls without authorization
- ❌ Scraping domains that have disallowed our user-agent in robots.txt
- ❌ Making requests faster than the domain's crawl-delay directive
- ❌ Storing personally identifiable information (PII) about end consumers
- ❌ Reproducing copyrighted product descriptions verbatim without transformation
- ❌ Reverse-engineering any API or mobile app
- ❌ Using scraped data to train ML models without proper licensing

---

## Data Attribution

Every record stored in the database includes:
- `source_name`: which connector collected it
- `source_url`: original URL (if applicable)
- `collected_at`: UTC timestamp of collection
- `legal_status`: connector's legal classification

---

## GDPR Considerations

- No personal data about EU consumers is collected
- No cookies or tracking identifiers are used
- Data subjects are product listings, not individuals
- Aggregate trend data does not constitute personal data under GDPR Article 4

---

## API Terms of Service Compliance

### Etsy API
- Data used for: trend analysis and competitive research
- Not used for: reselling data, building competing marketplace
- Attribution: "Data sourced from Etsy via official API"
- Rate limits: respected per Etsy API documentation

### Pinterest API
- Data used for: trend signal collection
- Not used for: building a Pinterest clone or scraping user data
- Attribution: "Trend data sourced from Pinterest via official API"
- Rate limits: respected per Pinterest API documentation

---

## Incident Response

If a data source sends a legal notice or cease-and-desist:
1. Immediately disable the connector via `connector_configs` table
2. Delete collected data from that source from the database
3. Document the incident in the source's legal_notes field
4. Do not re-enable without legal review

The `connector_configs.enabled` field can be set to `false` to immediately halt any connector without code changes.

---

## Stub Connectors

Connectors for legally uncertain sources are implemented as **stubs** — they have the correct interface but return mock data and make no external requests. Stubs are clearly marked:
- `legal_status = "stub"` in connector metadata
- Comment in code: `# STUB: Replace with official API when available`
- Dashboard shows "STUB" badge next to connector name
- All data from stubs is tagged with `is_mock = true` in database
