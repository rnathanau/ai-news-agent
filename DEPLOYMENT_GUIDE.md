# Deployment Guide - Render

This guide walks you through deploying your AI News Agent to Render.

## Prerequisites

1. GitHub account with your repository pushed
2. Render account (free tier available at https://render.com)
3. Your OpenAI API key (or Google/OpenRouter)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your latest changes are pushed to GitHub:

```bash
git add .
git commit -m "Updated README and render.yaml for AI News Agent"
git push origin main
```

### 2. Create PostgreSQL Database (Optional but Recommended)

1. Log in to Render Dashboard
2. Click "New +"
3. Select "PostgreSQL"
4. Choose a name: `ai-news-agent-db`
5. Select "Free" tier
6. Click "Create Database"
7. **Important**: Copy the "Internal Database URL" - you'll need this in step 4

### 3. Create Web Service

1. In Render Dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository:
   - If first time: Click "Connect Account" and authorize Render
   - Select your repository: `ai-news-agent`
4. Render will auto-detect `render.yaml` configuration

### 4. Configure Environment Variables

Render will create most variables from `render.yaml`, but you need to set the values:

#### Required Variables

| Variable | Value | How to Get |
|----------|-------|------------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `SECRET_KEY` | Auto-generated | Leave as is (Render generates this) |
| `DATABASE_URL` | `postgresql://...` | Copy from PostgreSQL database in Step 2 |

#### Optional Variables (for full functionality)

| Variable | Value | How to Get |
|----------|-------|------------|
| `SENDGRID_API_KEY` | `SG.` | Sign up at sendgrid.com |
| `FROM_EMAIL` | `notifications@yourdomain.com` | Your verified sender email |

**Note**: If you don't add a PostgreSQL database, the app will use SQLite (data will be lost on redeploy).

### 5. Deploy

1. Click "Create Web Service"
2. Render will:
   - Install dependencies (takes 2-3 minutes)
   - Start your application
   - Assign a URL: `https://ai-news-agent-XXXX.onrender.com`

3. Watch the logs for:
   ```
   INFO:     Application startup complete.
   Database initialized successfully
   Scheduler started
   ```

### 6. Test Your Deployment

1. Visit your Render URL
2. Click on the auth page: `https://your-app.onrender.com/auth.html`
3. Register a new account
4. Log in and test digest generation

## Troubleshooting

### Build Fails

**Error**: `Could not find a version that satisfies the requirement`

**Solution**: 
- Check Python version in render.yaml (should be 3.11.9)
- Verify all packages in requirements.txt are available

### Application Crashes on Startup

**Error**: `No module named 'backend'`

**Solution**: This should already be fixed! But if it happens:
- Make sure `rootDir: backend` is set in render.yaml
- Check that imports don't use `from backend.` prefix

### Environment Variables Not Working

**Error**: `KeyError: 'OPENAI_API_KEY'`

**Solution**:
1. Go to Render Dashboard
2. Select your web service
3. Go to "Environment" tab
4. Add missing variables manually
5. Click "Save Changes" (triggers redeploy)

### Database Connection Fails

**Error**: `could not connect to server`

**Solution**:
1. Verify `DATABASE_URL` is set correctly
2. Check PostgreSQL database is running
3. Use "Internal Database URL" not "External"

### Free Tier Limitations

**Important Notes**:
- Free tier spins down after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds (cold start)
- Consider upgrading to paid tier ($7/month) for 24/7 uptime
- Free PostgreSQL has 90-day data retention

## Updating Your Deployment

After making code changes:

```bash
# Commit and push
git add .
git commit -m "Your changes"
git push origin main

# Render auto-deploys if autoDeploy: true
# Or manually deploy from Render dashboard
```

## Custom Domain (Optional)

1. In Render Dashboard, go to your web service
2. Click "Settings"
3. Scroll to "Custom Domain"
4. Add your domain (e.g., `news.yourdomain.com`)
5. Add CNAME record in your DNS:
   - Name: `news`
   - Value: `your-app.onrender.com`

## Monitoring

### View Logs

1. Go to your web service in Render
2. Click "Logs" tab
3. Watch real-time application logs

### Metrics

1. Click "Metrics" tab
2. View:
   - CPU usage
   - Memory usage
   - Response times
   - Request volume

## Production Checklist

Before launching to real users:

- [ ] PostgreSQL database connected (not SQLite)
- [ ] `SECRET_KEY` is properly generated
- [ ] `OPENAI_API_KEY` is set and has credits
- [ ] `SENDGRID_API_KEY` is configured (for emails)
- [ ] `FROM_EMAIL` is verified in SendGrid
- [ ] Tested registration and login
- [ ] Tested digest generation
- [ ] Checked email delivery works
- [ ] Reviewed logs for errors
- [ ] Set up custom domain (optional)

## Cost Estimate

- **Render Web Service**: Free (or $7/month for always-on)
- **Render PostgreSQL**: Free (or $7/month for 1GB)
- **OpenAI API**: ~$0.01 per digest (GPT-4o-mini)
- **SendGrid**: Free for 100 emails/day

**Total**: $0-14/month + OpenAI usage

## Support

If deployment fails:
1. Check Render logs for error messages
2. Review this guide's troubleshooting section
3. Open an issue on GitHub with error logs
4. Contact Render support (good free tier support!)

---

**Deployment Issues?** Create an issue at: https://github.com/rnathanau/ai-news-agent/issues

