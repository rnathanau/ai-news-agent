# Deploy AI News Agent as a Render Blueprint

This is the **easiest and fastest** way to deploy! Everything is defined in `render.yaml` and deploys automatically.

## What is a Blueprint?

A Render Blueprint is infrastructure-as-code. One click deploys:
- ✅ PostgreSQL database
- ✅ FastAPI web service
- ✅ All configurations pre-set
- ✅ Auto-wiring between services

## Quick Deploy (3 Steps)

### Step 1: Click "Deploy to Render"

Visit your repository on GitHub and look for the **render.yaml** file, or click here:

👉 **[Deploy to Render](https://dashboard.render.com/select-repo?type=blueprint)**

### Step 2: Connect Repository

1. If first time: Authorize Render to access your GitHub
2. Select repository: `rnathanau/ai-news-agent`
3. Branch: `Daily-News-Digest`
4. Click "Connect"

### Step 3: Set Required Environment Variables

Render will detect `render.yaml` and show you the Blueprint. You only need to set **ONE required variable**:

| Variable | Value | Get it from |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key |

**Optional** (for full functionality):
- `SENDGRID_API_KEY` - For email delivery (get from SendGrid)
- `FROM_EMAIL` - Your sender email address

All other variables are auto-generated! 🎉

### Step 4: Deploy

Click **"Create Blueprint"** and Render will:

1. ⏱️ Create PostgreSQL database (30 seconds)
2. ⏱️ Build web service (2-3 minutes)
3. ✅ Auto-connect database to web service
4. ✅ Start your application

## What Gets Deployed

### Database: `ai-news-agent-db`
- Type: PostgreSQL 15
- Plan: Free tier (1GB storage, 90-day retention)
- Database name: `newsagent`
- **Automatically** connected to web service

### Web Service: `ai-news-agent`
- Type: Python web service
- Plan: Free tier (512MB RAM)
- Auto-deploy: Enabled (pushes to branch auto-deploy)
- URL: `https://ai-news-agent-XXXX.onrender.com`

## After Deployment

### 1. Check Deployment Status

1. Go to Render Dashboard
2. You'll see both services:
   - `ai-news-agent-db` (should show "Available")
   - `ai-news-agent` (should show "Live")

### 2. View Your Application

Click on `ai-news-agent` service to see:
- **URL**: Your live app URL
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, requests

### 3. Test Your Application

Visit your URL:
```
https://ai-news-agent-XXXX.onrender.com
```

Try these endpoints:
- `/` - Home page
- `/auth.html` - Register/Login
- `/docs` - API documentation

### 4. Register Your First User

1. Go to `/auth.html`
2. Create an account
3. Log in
4. Configure your location in Settings
5. Generate your first digest!

## Blueprint Features

### ✅ What's Automated

- Database creation and configuration
- Database connection string injection
- Environment variable generation (`SECRET_KEY`, PostgreSQL password)
- Service health checks
- Auto-restart on failure
- HTTPS certificates

### 🔧 What You Control

- **Auto-deploy**: Pushes to GitHub automatically redeploy (can disable)
- **Scaling**: Upgrade from free to paid plans anytime
- **Environment variables**: Update in Render dashboard
- **Rollback**: Revert to previous deployments with one click

## Updating Your Deployment

After making code changes:

```bash
# Just push to GitHub
git add .
git commit -m "Your changes"
git push origin Daily-News-Digest

# Render auto-deploys! ✨
```

Watch the deployment in Render Dashboard > Logs.

## Managing Your Blueprint

### View All Services

```
Dashboard → Blueprints → ai-news-agent
```

You'll see:
- All services in the blueprint
- Last deployment time
- Quick links to logs and settings

### Update Environment Variables

```
Service → Environment → Add Variable → Save Changes
```

This triggers an automatic redeploy.

### Scale Up (Optional)

Free tier limitations:
- ⏰ Spins down after 15 min inactivity
- 🐌 Cold start: 30-60 seconds on first request
- 💾 512MB RAM

To upgrade:
```
Service → Settings → Plan → Select Paid Plan ($7/month)
```

Benefits:
- ✅ Always on (no cold starts)
- ✅ More RAM/CPU
- ✅ Custom domains
- ✅ Better support

## Troubleshooting

### Blueprint Deployment Failed

**Error**: "Failed to create database"

**Solution**: 
- Render free tier limits: 1 PostgreSQL per account
- Delete unused databases or upgrade plan

---

**Error**: "Build failed: requirements.txt not found"

**Solution**:
- Ensure `rootDir: backend` in render.yaml
- Check requirements.txt exists in backend/

---

**Error**: "Environment variable OPENAI_API_KEY not set"

**Solution**:
1. Go to Render Dashboard
2. Click `ai-news-agent` service
3. Environment tab
4. Add `OPENAI_API_KEY`
5. Save (triggers redeploy)

### Application Won't Start

Check the logs:

```
Service → Logs (live tail)
```

Common issues:
- ❌ Missing `OPENAI_API_KEY` → Add in Environment
- ❌ Database connection failed → Check `DATABASE_URL` is auto-set
- ❌ Import errors → Should be fixed (we corrected imports)

### Database Connection Issues

The `DATABASE_URL` should be **automatically set** by the Blueprint. If it's not:

1. Go to `ai-news-agent-db` database
2. Copy the "Internal Connection String"
3. Go to `ai-news-agent` service
4. Environment → Add `DATABASE_URL` manually
5. Paste the connection string

## Monitoring

### View Logs

```
Service → Logs
```

Look for:
```
INFO:     Application startup complete.
Database initialized successfully
Scheduler started
```

### View Metrics

```
Service → Metrics
```

Monitor:
- Request volume
- Response times
- Memory usage
- CPU usage

### Set Up Notifications

```
Service → Settings → Notifications
```

Get alerted for:
- Deploy failures
- Service crashes
- High error rates

## Cost Breakdown

### Free Tier (Perfect for Personal Use)

| Service | Cost | Limits |
|---------|------|--------|
| Web Service | $0 | 512MB RAM, sleeps after 15min |
| PostgreSQL | $0 | 1GB storage, 90-day retention |
| OpenAI API | ~$0.01/digest | Pay per use |
| SendGrid | $0 | 100 emails/day |
| **Total** | **$0/month** | + OpenAI usage |

### Paid Tier (Recommended for Production)

| Service | Cost | Benefits |
|---------|------|----------|
| Web Service | $7/month | Always on, faster, more RAM |
| PostgreSQL | $7/month | 10GB storage, persistent |
| **Total** | **$14/month** | + OpenAI usage |

## Advanced Blueprint Configuration

### Add Redis (Optional)

Add to `render.yaml`:

```yaml
services:
  - type: redis
    name: ai-news-agent-cache
    plan: free
    maxmemoryPolicy: allkeys-lru
```

Then reference in web service:
```yaml
- key: REDIS_URL
  fromService:
    type: redis
    name: ai-news-agent-cache
    property: connectionString
```

### Add Cron Job (Optional)

For scheduled digest generation:

```yaml
services:
  - type: cron
    name: daily-digest-cron
    env: python
    schedule: "0 7 * * *"  # 7 AM daily
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/generate_digests.py
```

## Blueprint vs Manual Setup

| Feature | Blueprint | Manual |
|---------|-----------|--------|
| Setup time | 3 minutes | 15 minutes |
| Database setup | Automatic | Manual |
| Configuration | Pre-defined | Custom |
| Updates | Git push | Manual redeploy |
| Rollback | One click | Manual |
| Best for | Quick start | Custom needs |

**Recommendation**: Use Blueprint! It's faster and more reliable.

## Next Steps

1. ✅ Deploy using Blueprint (you are here!)
2. 📧 Set up SendGrid for email delivery
3. 🌐 Add custom domain (optional)
4. 📊 Monitor usage and costs
5. 🚀 Scale up when ready for production

## Support

- **Render Docs**: https://render.com/docs/blueprints
- **Our Docs**: See DEPLOYMENT_GUIDE.md for detailed troubleshooting
- **Issues**: https://github.com/rnathanau/ai-news-agent/issues

---

**Deploy in 3 minutes!** 👉 [Start Now](https://dashboard.render.com/select-repo?type=blueprint)

