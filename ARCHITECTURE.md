# Architecture Document — Jewelry Trend Engine

**Version:** 1.0  
**Date:** 2026-05-25

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                     │
│  Google Trends │ Etsy API │ Pinterest API │ Web (compliant) │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  CONNECTOR LAYER (Python)                    │
│  base.py interface → normalize → validate → save            │
│  Runs on: Railway Cron / standalone scripts                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DATABASE (Supabase / PostgreSQL)                │
│  products │ trend_signals │ opportunity_scores │ reports     │
│  SQLAlchemy (async) │ Alembic migrations                    │
└──────────┬──────────────────────────┬────────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌───────────────────────────────────┐
│  AI ANALYSIS     │      │         BACKEND API               │
│  Anthropic Claude│      │  FastAPI (async) on Railway       │
│  - extract attrs │      │  /api/products                    │
│  - detect trends │      │  /api/trends                      │
│  - score opps    │      │  /api/opportunities               │
│  - gen reports   │      │  /api/reports                     │
└──────────┬───────┘      │  /api/connectors                  │
           │              │  /api/settings                    │
           └──────────────┴────────────────┬────────────────────┘
                                           │
                    ┌──────────────────────┤
                    │                      │
                    ▼                      ▼
┌───────────────────────┐    ┌────────────────────────────────┐
│  STREAMLIT DASHBOARD  │    │  NOTIFICATIONS                 │
│  Streamlit Cloud      │    │  Resend (email)                │
│  8 pages, Turkish     │    │  Slack (webhook)               │
│  Read-only from API   │    │  Supabase Storage (reports)    │
└───────────────────────┘    └────────────────────────────────┘
```

---

## Cloud Services Map

| Layer | Service | Technology |
|-------|---------|------------|
| Database | Supabase | PostgreSQL 15 |
| File Storage | Supabase Storage | S3-compatible |
| Cache | Upstash Redis | Serverless Redis |
| Backend API | Railway | Python 3.12 / FastAPI |
| Background Jobs | Railway Cron | Python scripts |
| Dashboard | Streamlit Cloud | Streamlit |
| AI | Anthropic | Claude claude-3-5-sonnet-20241022 |
| Email | Resend | HTTP API |
| Notifications | Slack | Incoming Webhooks |

---

## Data Flow

### Ingestion Flow (every 6 hours)
```
Railway Cron → run_connectors.py
  → foreach enabled connector:
      connector.fetch()         # raw data from source
      connector.normalize()     # → ProductData schema
      connector.validate()      # completeness check
      connector.save()          # → Supabase products table
  → log run in source_runs table
  → trigger run_scoring.py
```

### AI Analysis Flow (after ingestion)
```
run_scoring.py
  → fetch new products (status = 'raw')
  → ai.tasks.extract_product_attributes()
      → Claude API call
      → store result in products table + log ai call
  → ai.tasks.detect_trend_patterns()
      → batch analysis of recent products
      → store in trend_signals table
  → scoring.score_products()
      → composite score calculation
      → store in opportunity_scores table
  → update product status = 'scored'
```

### Reporting Flow (daily/weekly)
```
Railway Cron → generate_daily_report.py / generate_weekly_report.py
  → fetch scored products and trend signals
  → ai.tasks.generate_report()
      → Claude generates Turkish markdown report
  → storage.save_report()
      → upload to Supabase Storage
      → insert record in reports table
  → alerts.send_report()
      → Resend email to ALERT_EMAIL_TO
      → Slack summary to SLACK_WEBHOOK_URL
```

---

## Database Schema

### Core Tables

```sql
brands              -- brand profiles
competitors         -- tracked competitor brands
sources             -- data source registry
source_runs         -- connector execution log
products            -- normalized product records
product_snapshots   -- price/availability history
categories          -- jewelry categories
materials           -- material taxonomy
stones              -- stone/gem taxonomy
colors              -- color taxonomy
style_tags          -- style descriptor tags
image_assets        -- product images
trend_signals       -- trend detection results
opportunity_scores  -- composite scoring results
reports             -- generated report metadata
alerts              -- alert conditions and history
connector_configs   -- per-connector settings
app_settings        -- global app configuration
```

### Key Relationships
```
products → categories (many-to-one)
products → materials (many-to-many via junction)
products → stones (many-to-many via junction)
products → style_tags (many-to-many via junction)
products → opportunity_scores (one-to-many)
products → product_snapshots (one-to-many)
source_runs → sources (many-to-one)
trend_signals → products (many-to-many)
```

---

## API Structure

```
GET  /health                          # health check
GET  /api/v1/products                 # list products (paginated, filterable)
GET  /api/v1/products/{id}            # single product detail
GET  /api/v1/trends                   # trend signals
GET  /api/v1/opportunities            # scored opportunities
GET  /api/v1/opportunities/top        # top N opportunities
GET  /api/v1/reports                  # list reports
POST /api/v1/reports/generate         # trigger report generation
GET  /api/v1/connectors               # list connectors with status
POST /api/v1/connectors/{name}/run    # manually trigger connector
GET  /api/v1/settings                 # get app settings
PATCH /api/v1/settings                # update app settings
GET  /api/v1/competitors              # list competitors
GET  /api/v1/stats/overview           # dashboard overview stats
```

---

## Security Architecture

- **Service Role Key**: only in backend Railway environment (never in dashboard)
- **Anon Key**: used in dashboard for read-only public data
- **RLS Policies**: all tables have Row Level Security enabled
- **No secrets in code**: all config via environment variables
- **HTTPS only**: enforced by Railway and Streamlit Cloud
- **Rate limiting**: per-connector and per-domain rate limiters

---

## Connector Architecture

Each connector extends `BaseConnector`:

```python
class BaseConnector(ABC):
    name: str
    legal_status: Literal["official_api", "public_allowed", "stub", "mock"]
    enabled: bool
    rate_limit_seconds: float
    
    async def fetch(self) -> list[RawData]
    async def normalize(self, raw: RawData) -> ProductData
    async def validate(self, product: ProductData) -> bool
    async def save(self, products: list[ProductData]) -> int
    async def run(self) -> ConnectorResult
```

---

## AI Prompt Architecture

All prompts are versioned Markdown templates in `/prompts/`:

| File | Task | Output |
|------|------|--------|
| product_extractor.md | Extract structured attributes | JSON |
| image_analyzer.md | Analyze product images | JSON |
| trend_detector.md | Detect emerging patterns | JSON |
| opportunity_scorer.md | Score and narrate opportunity | JSON |
| report_generator_tr.md | Generate Turkish report | Markdown |
| competitor_analyzer.md | Analyze competitor products | JSON |

Each AI call logs: model, prompt_version, input_tokens, output_tokens, latency_ms, timestamp.

---

## Caching Strategy

Upstash Redis is used for:
- Dashboard overview stats (TTL: 5 minutes)
- Connector last-run status (TTL: 1 hour)
- AI analysis results for duplicate products (TTL: 24 hours)
- Rate limit counters per domain

---

## Deployment Architecture

```
GitHub Repository (single repo)
├── /backend → Railway service (FastAPI + jobs)
├── /dashboard → Streamlit Community Cloud
└── /migrations → run manually via Railway one-off job
```

All services pull from the same GitHub repo. Environment variables are set per-service in Railway and Streamlit dashboards.
