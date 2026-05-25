# Cloud Deployment Guide — Jewelry Trend Engine

## Overview

The system deploys across 5 cloud services from a single GitHub repository:

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| Supabase | Database + Storage | Free tier |
| Upstash Redis | Cache | Free tier |
| Railway | Backend API + Cron Jobs | ~$5/month |
| Streamlit Cloud | Dashboard | Free tier |
| Anthropic | AI analysis | Pay per use |

**Total estimated cost: ~$5-15/month depending on AI usage.**

---

## Step 1 — Supabase Setup

1. Go to [supabase.com](https://supabase.com) → "New Project"
2. Choose a region close to your users (e.g., Frankfurt for Europe)
3. Set a strong database password and save it

4. Get your API keys:
   - Go to **Settings → API**
   - Copy: `Project URL`, `anon public`, `service_role secret`

5. Get the database connection string:
   - Go to **Settings → Database → Connection String**
   - Copy the **URI** format
   - Replace `[YOUR-PASSWORD]` with your database password
   - This is your `DATABASE_URL`

6. Create the Storage bucket:
   - Go to **Storage → New Bucket**
   - Name: `reports`
   - Set to **Public**
   - Click Create

7. Run migrations:
   ```bash
   # Set DATABASE_URL in your .env first
   pip install alembic asyncpg psycopg2-binary
   alembic upgrade head
   ```

8. Seed demo data:
   ```bash
   pip install -r backend/requirements.txt
   python data/seed/seed.py
   ```

---

## Step 2 — Upstash Redis Setup

1. Go to [console.upstash.com](https://console.upstash.com)
2. Click **Create Database**
3. Select **Redis** → Global (multi-region)
4. Name: `jewelry-trend-cache`
5. After creation, go to **REST API** tab
6. Copy: `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`

---

## Step 3 — Railway Backend Deploy

1. Go to [railway.app](https://railway.app) → **New Project**
2. Select **Deploy from GitHub repo**
3. Select your `jewelry-trend-engine` repository
4. Railway will detect it as a Python project

5. Set Root Directory: `backend`
6. Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

7. Add environment variables (Settings → Variables):
   ```
   DATABASE_URL=...
   SUPABASE_URL=...
   SUPABASE_ANON_KEY=...
   SUPABASE_SERVICE_ROLE_KEY=...
   UPSTASH_REDIS_REST_URL=...
   UPSTASH_REDIS_REST_TOKEN=...
   ANTHROPIC_API_KEY=...
   AI_MODEL=claude-3-5-sonnet-20241022
   RESEND_API_KEY=...
   SLACK_WEBHOOK_URL=...
   ALERT_EMAIL_FROM=...
   ALERT_EMAIL_TO=...
   BRAND_NAME=Your Brand Name
   APP_ENV=production
   ```

8. Deploy. Railway will give you a URL like `https://your-app.railway.app`
9. Copy this URL — you'll need it for the dashboard (`API_BASE_URL`)

---

## Step 4 — Railway Cron Jobs

In Railway, add three Cron Job services (Settings → Cron):

| Job | Schedule | Command |
|-----|----------|---------|
| Run Connectors | `0 */6 * * *` | `python /app/jobs/run_connectors.py` |
| Daily Report | `0 5 * * *` | `python /app/jobs/generate_daily_report.py` |
| Weekly Report | `0 6 * * 1` | `python /app/jobs/generate_weekly_report.py` |

Note: Times are UTC. 05:00 UTC = 08:00 Istanbul (UTC+3).

For each Cron Job:
1. Click **New Service → Cron Job**
2. Connect to same GitHub repo
3. Set Root Directory: `backend`
4. Set the same environment variables as the main service
5. Set the schedule and command

---

## Step 5 — Streamlit Cloud Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New App**
4. Settings:
   - Repository: `your-username/jewelry-trend-engine`
   - Branch: `main`
   - Main file path: `dashboard/app.py`

5. Add secrets (Advanced Settings → Secrets):
   ```toml
   API_BASE_URL = "https://your-app.railway.app"
   ```

6. Click Deploy

---

## Step 6 — Resend Email Setup

1. Go to [resend.com](https://resend.com) → Sign up (free)
2. Go to **API Keys** → Create API Key
3. Copy the key → `RESEND_API_KEY`
4. Verify your sending domain (or use the sandbox for testing)
5. Set `ALERT_EMAIL_FROM` to your verified domain address

---

## Step 7 — Slack Webhook Setup

1. Go to your Slack workspace
2. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
3. Choose **From scratch** → Name it "Jewelry Trend Alerts"
4. Select your workspace
5. Go to **Incoming Webhooks** → Turn it On
6. Click **Add New Webhook to Workspace**
7. Select the channel to post to
8. Copy the Webhook URL → `SLACK_WEBHOOK_URL`

---

## Verification Checklist

After deployment, verify each component:

- [ ] `GET https://your-app.railway.app/health` returns `{"status": "ok"}`
- [ ] `GET https://your-app.railway.app/api/v1/connectors` returns connector list
- [ ] Streamlit dashboard loads and shows data
- [ ] Trigger mock connector from dashboard → products appear
- [ ] Generate test report → appears in Reports page
- [ ] Send test Slack message via `/api/v1/reports/generate`
- [ ] Receive test email

---

## Troubleshooting

**Railway build fails:**
- Check that `backend/requirements.txt` has all packages
- Check Python version: Railway uses 3.12 by default

**Database connection fails:**
- Verify `DATABASE_URL` uses `postgresql+asyncpg://` scheme
- Check Supabase project is not paused (free tier pauses after 1 week of inactivity)

**Dashboard can't connect to API:**
- Verify `API_BASE_URL` in Streamlit secrets has no trailing slash
- Check Railway app is running (not crashed)

**Cron jobs not running:**
- Check Railway dashboard for cron job logs
- Verify the command path is correct
