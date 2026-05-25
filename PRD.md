# Product Requirements Document — Jewelry Trend Engine

**Version:** 1.0  
**Date:** 2026-05-25  
**Status:** Active Development

---

## 1. Product Overview

Jewelry Trend Engine is an always-on, cloud-native AI research system that continuously monitors jewelry market trends, competitor products, and consumer demand signals. It surfaces actionable insights to help jewelry brands decide what to design, restock, test, or promote next.

### Problem Statement

Jewelry brands make collection and inventory decisions based on intuition and delayed market feedback. By the time a brand notices a trend through sales data, early adopters have moved on. There is no affordable, automated system that aggregates multi-source trend signals and translates them into structured product opportunities.

### Solution

A fully automated pipeline that:
1. Collects product and trend data from multiple sources (Google Trends, Etsy, Pinterest, competitor sites, manual uploads)
2. Normalizes and stores all data in a structured database
3. Uses AI (Claude) to extract product attributes, detect patterns, and score opportunities
4. Delivers weekly and daily reports in Turkish via email and Slack
5. Provides a live dashboard for exploration and analysis

---

## 2. Target Users

### Primary User
- **Jewelry Brand Owner / Product Manager** (Turkey + Europe market)
- Non-technical, reads Turkish
- Checks dashboard weekly, reads email reports daily
- Makes collection and inventory decisions based on insights

### Secondary User
- **Brand Analyst / Marketing Manager**
- Uses the dashboard for deeper exploration
- Exports data to CSV for presentations

---

## 3. Scope — MVP

### In Scope
- Multi-source data ingestion (6 connector types)
- PostgreSQL data storage via Supabase
- AI-powered product attribute extraction
- Trend pattern detection and opportunity scoring
- Streamlit dashboard (8 pages, Turkish UI)
- Daily + weekly reports in Turkish
- Email (Resend) and Slack notification delivery
- Scheduled background jobs
- Demo/mock mode (works without API keys)

### Out of Scope (Post-MVP)
- Mobile app
- User authentication / multi-tenant
- Direct e-commerce platform integration (Shopify, WooCommerce)
- Real-time price tracking
- Social media posting automation
- Custom ML model training

---

## 4. Functional Requirements

### FR-01: Data Collection
- System SHALL collect jewelry product data every 6 hours
- Each connector SHALL be independently enable/disable-able
- All data SHALL record source name and collection timestamp
- System SHALL check robots.txt before any web scraping
- Rate limiting SHALL be enforced: minimum 3 seconds between requests to same domain

### FR-02: Data Storage
- All raw and normalized product data SHALL be stored in Supabase PostgreSQL
- Product snapshots SHALL track price and availability changes over time
- All AI outputs SHALL be stored with model version, token count, and timestamp

### FR-03: AI Analysis
- System SHALL extract structured attributes from every product (material, stone, style, category, color, price tier)
- System SHALL detect trending patterns across product batches weekly
- System SHALL generate opportunity scores 0-100 for each product cluster
- All AI analysis SHALL be performed using Anthropic Claude API

### FR-04: Opportunity Scoring
- Every product/trend cluster SHALL receive a composite score 0-100
- Score weights SHALL be configurable via dashboard settings
- Score breakdown SHALL be stored per product (not just final score)

### FR-05: Reporting
- System SHALL generate daily summaries in Turkish every day at 08:00 UTC+3
- System SHALL generate weekly full trend reports every Monday at 09:00 UTC+3
- Reports SHALL be stored as Markdown files in Supabase Storage
- Reports SHALL be sent via email (Resend) and summarized to Slack

### FR-06: Dashboard
- Dashboard SHALL display real-time data from Supabase
- Dashboard SHALL support filtering by category, material, style, score, source, date
- Dashboard SHALL allow CSV export of any table
- Dashboard SHALL show connector status with last run time and error count

### FR-07: Configuration
- All brand profile settings SHALL be editable via dashboard
- All scoring weights SHALL be adjustable via sliders
- All connector enable/disable toggles SHALL be functional
- Settings SHALL persist in app_settings database table

---

## 5. Non-Functional Requirements

### Performance
- API response time: < 2 seconds for dashboard queries
- Connector runs: < 5 minutes per connector per cycle
- AI analysis: batch processed asynchronously

### Reliability
- Each job SHALL be independently runnable (no dependencies between jobs)
- Failed connector runs SHALL be logged and retried on next cycle
- System SHALL operate in demo mode without any external API keys

### Legal Compliance
- All data collection SHALL comply with source robots.txt
- No CAPTCHA bypassing, no authentication wall bypassing
- API-based sources SHALL use official APIs only
- All data sources SHALL be documented with legal status

### Security
- No secrets in code — all via environment variables
- Supabase Row Level Security policies enabled
- Service role key used only in backend, never in dashboard

---

## 6. Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Products tracked per week | > 500 |
| Trend signals identified per week | > 50 |
| Report generation success rate | > 95% |
| Dashboard load time | < 3 seconds |
| Demo mode works without any API keys | 100% |

---

## 7. Assumptions

See ASSUMPTIONS.md for full list.

---

## 8. Compliance

See COMPLIANCE.md for full legal and ethical compliance documentation.
