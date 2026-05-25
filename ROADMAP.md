# Roadmap — Jewelry Trend Engine

---

## MVP (Current) — Target: Week 1-2

**Goal:** Working system in demo mode with all major features functional.

### Deliverables
- All 6 data connectors (4 with stubs, mock always works)
- Full database schema with migrations
- FastAPI backend with all endpoints
- Streamlit dashboard (8 pages)
- AI analysis pipeline (Claude)
- Daily + weekly reports in Turkish
- Email + Slack notifications
- Opportunity scoring engine
- Demo mode (no API keys required)

---

## v1.1 — Live API Integration — Target: Week 3-4

**Goal:** Connect real data sources, get real trend signals.

### Deliverables
- [ ] Etsy API v3 integration (real listings)
- [ ] Google Trends connector fully operational
- [ ] Supabase Edge Function for lightweight jobs
- [ ] First real weekly report generated and sent
- [ ] Dashboard showing real trend data

---

## v1.2 — Pinterest + Enrichment — Target: Month 2

**Goal:** More data sources, richer AI analysis.

### Deliverables
- [ ] Pinterest API v5 access approved and integrated
- [ ] Image visual analysis via Claude vision
- [ ] Product deduplication across sources
- [ ] Trend velocity scoring with historical comparison
- [ ] Competitor tracking from Etsy seller data

---

## v1.3 — Advanced Reporting — Target: Month 3

**Goal:** Reports good enough to drive real business decisions.

### Deliverables
- [ ] PDF report generation (via reportlab or weasyprint)
- [ ] Report templates customizable in dashboard
- [ ] Seasonal trend calendar
- [ ] "New vs Seen Before" novelty tracking
- [ ] Price trend analysis with historical charts

---

## v2.0 — Multi-Tenant & Automation — Target: Month 4-6

**Goal:** Platform ready for multiple jewelry brands.

### Deliverables
- [ ] Supabase Auth — user login
- [ ] Multi-tenant data isolation
- [ ] Brand profile per tenant
- [ ] Custom connector configuration per brand
- [ ] Webhook-based real-time alerts
- [ ] Shopify / WooCommerce integration for catalog sync
- [ ] Mobile-friendly dashboard
- [ ] API key management UI

---

## Post-MVP Wishlist

- AI-generated product photography prompts (Midjourney/DALL-E)
- TikTok and Instagram Reels trend analysis
- Demand forecasting with time-series ML
- Direct publishing to Shopify draft products
- Slack bot interface for ad-hoc queries
- Custom ML fine-tuning on brand-specific data
