# Deployment Options

Choose the deployment option that fits your needs:

## 📊 Quick Comparison

| Option | Cost | Data Persistence | Best For |
|--------|------|------------------|----------|
| **Free Tier (SQLite)** | $0/month | ⚠️ Ephemeral* | Testing, demos |
| **Paid Tier (PostgreSQL)** | $14/month | ✅ Persistent | Production use |

*Ephemeral = Data is lost when service redeploys or restarts

---

## Option 1: Free Tier (SQLite) - $0/month

**Use file:** `render.yaml`

### ✅ Pros
- Completely free
- Simple setup (no database service)
- Perfect for testing and demos
- Fast deployment (2-3 minutes)

### ⚠️ Cons
- **Data is lost on redeploy** (users, digests, settings)
- Service spins down after 15 min inactivity
- Cold start: 30-60 seconds on first request
- 512MB RAM limit

### 📝 Data Persistence Note
On Render's free tier:
- SQLite data is stored in the container filesystem
- Container filesystem is **ephemeral** (temporary)
- Data is **reset** when:
  - You push new code (auto-deploy)
  - Service restarts
  - Render maintenance occurs

### 🎯 Use Cases
- ✅ Testing the application
- ✅ Demo for stakeholders
- ✅ Learning/experimentation
- ❌ Production use
- ❌ Storing important user data

### 🚀 Deploy Free Tier

1. **Deploy via Blueprint:**
   - Go to: https://dashboard.render.com/select-repo?type=blueprint
   - Select: `rnathanau/ai-news-agent`
   - Branch: `Daily-News-Digest`

2. **Set Environment Variables:**
   - `OPENAI_API_KEY` = Your API key

3. **Click "Create Blueprint"**

4. **Done!** Your app will be live in 2-3 minutes

---

## Option 2: Paid Tier (PostgreSQL) - $14/month

**Use file:** `render-postgres.yaml`

### ✅ Pros
- **Full data persistence** (never lost)
- Always-on (no cold starts)
- Better performance (more RAM/CPU)
- Suitable for real users
- Automatic backups

### 💰 Costs
- Web Service: $7/month (Starter plan)
- PostgreSQL: $7/month (Starter plan)
- **Total: $14/month** (+ OpenAI API usage)

### 🎯 Use Cases
- ✅ Production deployment
- ✅ Real users with accounts
- ✅ Historical data needed
- ✅ Daily digests for yourself/family
- ✅ Portfolio project

### 🚀 Deploy Paid Tier

1. **Rename the config file:**
   ```bash
   cd ai-news-agent
   mv render.yaml render-free.yaml.bak
   mv render-postgres.yaml render.yaml
   git add .
   git commit -m "Switch to PostgreSQL deployment"
   git push
   ```

2. **Deploy via Blueprint:**
   - Go to: https://dashboard.render.com/select-repo?type=blueprint
   - Select: `rnathanau/ai-news-agent`
   - Render detects the updated `render.yaml`

3. **Set Environment Variables:**
   - `OPENAI_API_KEY` = Your API key
   - (Optional) `SENDGRID_API_KEY` for emails

4. **Click "Create Blueprint"**

5. **Render creates:**
   - PostgreSQL database (persistent)
   - Web service (always-on)
   - Auto-connects them

---

## Option 3: Hybrid Approach

Start free, upgrade later when needed:

### Phase 1: Free Tier Testing (Weeks 1-2)
1. Deploy with `render.yaml` (free tier)
2. Test all features
3. Register test accounts
4. Generate sample digests
5. Verify everything works

### Phase 2: Upgrade to Production (Week 3+)
1. Switch to `render-postgres.yaml`
2. Redeploy
3. Re-register accounts (data doesn't migrate)
4. Now have persistent production app

**Note:** You'll need to recreate user accounts when upgrading (data doesn't transfer).

---

## Deployment Files Explained

| File | Database | Plan | Data Persistence |
|------|----------|------|------------------|
| `render.yaml` | SQLite | Free | Ephemeral |
| `render-sqlite.yaml` | SQLite | Free | Ephemeral |
| `render-postgres.yaml` | PostgreSQL | Paid ($14) | Persistent |

---

## Quick Decision Guide

### Choose FREE if:
- 🧪 Just testing the app
- 📚 Learning deployment
- 🎨 Creating a demo
- 💸 Budget is $0
- ⏰ Okay with losing data

### Choose PAID if:
- 🚀 Deploying for real use
- 👥 Have actual users
- 📊 Need historical data
- 💼 Portfolio/resume project
- ⚡ Need 24/7 uptime

---

## Deployment Instructions

### Using render.yaml (Free - Default)

```bash
# Already configured - just deploy!
# Go to: https://render.com/deploy?repo=https://github.com/rnathanau/ai-news-agent
```

### Using render-postgres.yaml (Paid)

```bash
# In your local repository
git mv render.yaml render-free.yaml
git mv render-postgres.yaml render.yaml
git add .
git commit -m "Switch to PostgreSQL for persistent data"
git push origin Daily-News-Digest

# Then deploy via Render Dashboard
```

---

## Cost Breakdown

### Free Tier
| Service | Cost |
|---------|------|
| Web Service | $0 |
| Database (SQLite) | $0 |
| OpenAI API | ~$0.01/digest |
| SendGrid Email | $0 (100/day) |
| **Total** | **$0/month** + API usage |

### Paid Tier
| Service | Cost |
|---------|------|
| Web Service (Starter) | $7/month |
| PostgreSQL (Starter) | $7/month |
| OpenAI API | ~$0.01/digest |
| SendGrid Email | $0 (100/day) |
| **Total** | **$14/month** + API usage |

### Estimated API Costs
- **1 digest/day**: ~$0.30/month
- **Personal use** (1 user): ~$14.30/month total
- **5 users**: ~$15.50/month total

---

## FAQ

### Q: Will my data be safe on free tier?
**A:** No. Data is ephemeral and will be lost on redeploys. Use paid tier for data persistence.

### Q: Can I migrate from free to paid later?
**A:** Yes, but you'll need to recreate accounts (data doesn't migrate automatically).

### Q: How often does free tier redeploy?
**A:** Whenever you push code changes (if auto-deploy is on) or during Render maintenance.

### Q: Can I use PostgreSQL on free tier?
**A:** Render offers 1 free PostgreSQL, but it has a 90-day data retention limit.

### Q: What about paid tier with SQLite?
**A:** Paid tier ($7 web service) supports persistent disks, so SQLite data would persist. But PostgreSQL is better for $14 total.

---

## Recommendation

**For testing:** Use `render.yaml` (free tier)
**For production:** Use `render-postgres.yaml` (paid tier)

---

## Support

- Issues: https://github.com/rnathanau/ai-news-agent/issues
- Render Docs: https://render.com/docs






