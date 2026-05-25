# Assumptions — Jewelry Trend Engine

**Date:** 2026-05-25

---

## Technical Assumptions

### A-01: Cloud-Only Deployment
The system runs entirely on cloud services. There is no local machine, no Docker, no self-hosted database. All services are third-party SaaS platforms.

### A-02: Python 3.12 Runtime
All backend code is written for Python 3.12. Railway and Streamlit Cloud both support this version.

### A-03: Async-First Architecture
FastAPI and SQLAlchemy are used in async mode throughout. Background jobs use asyncio directly, not Celery or multiprocessing.

### A-04: Supabase PostgreSQL as Single Source of Truth
All persistent data lives in Supabase. The dashboard reads from the same database via the backend API (never direct DB connections from Streamlit).

### A-05: No Real-Time Requirements
Data freshness of 6 hours for ingestion and 24 hours for reports is acceptable for MVP. No WebSocket or real-time push needed.

### A-06: Upstash Redis for Caching Only
Redis is used purely for caching and rate limiting, not as a job queue or primary data store.

### A-07: Single-Tenant MVP
The MVP serves a single jewelry brand. Multi-tenancy is deferred to post-MVP. The `brand_id` foreign key is in the schema to support future multi-tenancy without migration.

### A-08: SQLAlchemy Async with asyncpg Driver
Database connections use `asyncpg` as the PostgreSQL driver with `sqlalchemy[asyncio]`.

---

## Business Assumptions

### B-01: Turkish is Primary Report Language
All generated reports, dashboard labels, and AI-generated content default to Turkish. English is available as a configurable alternative.

### B-02: Target Market
Primary market is Turkey + European Union. SEO keyword trends, competitor analysis, and price benchmarks are calibrated for these markets.

### B-03: Price Range
The typical product price range is 25–250 USD. Products outside this range are flagged but not excluded.

### B-04: Jewelry Categories
The system focuses on: rings, necklaces, bracelets, earrings, anklets. Watches and accessories are tracked but not primary.

### B-05: Competitor Data via Manual Upload
For MVP, competitor product data is uploaded manually as CSV/JSON. Direct competitor site scraping requires per-site legal review.

---

## API and Integration Assumptions

### C-01: Etsy API Key Required
The Etsy connector requires an Etsy Open API v3 key. Without this key, the connector falls back to a stub that returns mock data. Getting the key requires registering a developer app at etsy.com/developers.

### C-02: Pinterest API Requires Business Account
The Pinterest connector requires Pinterest API v5 access, which requires a Pinterest Business account. Without credentials, the connector falls back to a stub.

### C-03: Google Trends via pytrends
pytrends is an unofficial Python wrapper for Google Trends. It works without API keys but is subject to rate limiting. The system implements exponential backoff. If Google blocks access, the connector logs the error and retries on the next cycle.

### C-04: Resend Free Tier Limit
Resend free tier allows 100 emails/day and 3,000/month. For MVP with 1-2 emails/day this is sufficient.

### C-05: Slack Webhook is One-Way
Slack Incoming Webhooks only support sending messages. Reading Slack messages is out of scope.

### C-06: Anthropic API Rate Limits
Claude API has rate limits. The system batches AI calls and adds delays between requests. If rate limited, jobs retry with exponential backoff.

---

## Operational Assumptions

### D-01: Railway Cron Accuracy
Railway Cron Jobs trigger within ~1 minute of scheduled time. For MVP this is acceptable. If higher accuracy is needed, Upstash QStash can replace Railway Cron.

### D-02: Streamlit Cold Start
Streamlit Community Cloud apps may sleep after inactivity. Dashboard may take 10-30 seconds to wake up. This is acceptable for MVP.

### D-03: Supabase Storage Bucket
A public bucket named `reports` is created in Supabase Storage for report files. Bucket access policy is set to public read.

### D-04: Manual Migration Execution
Alembic migrations are run manually via a Railway one-off job or by the developer. Auto-migration on startup is disabled to prevent accidental data loss.

### D-05: Demo Mode
Without any external API keys, the system runs in demo mode using the mock connector. All features work; data is synthetic but realistic.
