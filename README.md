# Jewelry Trend Engine

An always-on, AI-powered product research system for jewelry brands. Continuously monitors Google Trends, Etsy, Pinterest, and competitor data to surface actionable insights about which jewelry styles, materials, and products are trending.

## Features

- **Multi-source data ingestion**: Google Trends, Etsy API, Pinterest API, manual CSV upload, compliant web scraping
- **AI analysis**: Product attribute extraction, trend detection, opportunity scoring (Claude claude-3-5-sonnet-20241022)
- **Opportunity scoring**: Composite 0-100 score with configurable weights
- **Turkish reports**: Daily and weekly AI-generated reports in Turkish
- **Live dashboard**: 8-page Streamlit dashboard with charts and filters
- **Notifications**: Email (Resend) + Slack alerts
- **Demo mode**: Works immediately without any external API keys

## Architecture

| Layer | Service |
|-------|---------|
| Database | Supabase (PostgreSQL) |
| Cache | Upstash Redis |
| Backend API | Railway (FastAPI) |
| Background Jobs | Railway Cron |
| Dashboard | Streamlit Community Cloud |
| AI | Anthropic Claude |
| Email | Resend |

## Quick Start (Demo Mode)

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Set only `ANTHROPIC_API_KEY` and `DATABASE_URL` (minimum required)
4. Set `DEMO_MODE=true` to skip all external data connectors
5. Run the backend: `cd backend && uvicorn main:app --reload`
6. Run the dashboard: `cd dashboard && streamlit run app.py`

## Cloud Deployment

See [docs/cloud_deployment.md](docs/cloud_deployment.md) for step-by-step deployment guides for all cloud services.

## Project Structure

```
├── backend/          # FastAPI application
├── dashboard/        # Streamlit dashboard
├── jobs/             # Scheduled job scripts
├── migrations/       # Alembic database migrations
├── prompts/          # AI prompt templates
├── data/seed/        # Demo data
├── tests/            # Test suite
└── docs/             # Deployment and usage guides
```

## Documentation

- [Product Requirements](PRD.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Compliance & Legal](COMPLIANCE.md)
- [Deployment Guide](docs/cloud_deployment.md)
- [Connector Docs](docs/connectors.md)
- [Scoring System](docs/scoring.md)

## License

Proprietary. All rights reserved.
