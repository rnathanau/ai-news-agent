# Deployment Instructions - News Relevancy Updates

## Quick Deployment (Render)

### Step 1: Get Tavily API Key (Free)

1. Go to https://tavily.com/
2. Click "Sign Up" or "Get Started"
3. Verify your email
4. Go to Dashboard → API Keys
5. Copy your API key (starts with `tvly-`)

**Free Tier**: 1,000 searches/month (plenty for daily digests)

### Step 2: Update Render Environment Variables

1. Go to https://dashboard.render.com/
2. Find your service: `ai-news-agent-foz7`
3. Click on the service name
4. Click **"Environment"** in left sidebar
5. Click **"Add Environment Variable"**
6. Add:
   - Key: `TAVILY_API_KEY`
   - Value: `tvly-xxxxxxxxxxxxxxxxx` (your API key)
7. Click **"Save Changes"**

### Step 3: Commit and Push Code

```bash
# Make sure you're in the project root
cd ai-news-agent

# Stage the changes
git add backend/main.py backend/requirements.txt IMPROVEMENTS_SUMMARY.md DEPLOYMENT_INSTRUCTIONS.md

# Commit with descriptive message
git commit -m "Improve news recency filtering and URL validation

- Add date filtering to Tavily API calls (last 2 days)
- Validate URLs to prevent fake/example links
- Enhanced relevance agent with strict date checking
- Remove LLM fallback fake URLs
- Add python-dateutil dependency"

# Push to GitHub
git push origin main
```

### Step 4: Monitor Deployment

1. Go back to Render dashboard
2. You'll see "Deploy started" notification
3. Click **"Logs"** tab to watch progress
4. Wait for: `Build successful` → `Deploy live`
5. Takes about 2-3 minutes

### Step 5: Test the Improvements

1. **Visit Your App**: https://ai-news-agent-foz7.onrender.com
2. **Login** with your credentials
3. **Generate a Digest**:
   - Go to Dashboard
   - Click "Generate Digest"
   - Wait 10-20 seconds
4. **Verify Quality**:
   - ✅ All URLs should be real news sites (not example.com)
   - ✅ All articles should be from last 1-2 days
   - ✅ Articles should be relevant to your location
   - ✅ Click "Read Full Story" links - they should work!

### Step 6: Check Logs (Optional)

1. In Render dashboard, click **"Logs"**
2. Look for messages like:
   ```
   [Tavily] Found 8 results
   [Tavily] Returning 5 recent articles
   [Monitor Agent] Found 5 real articles from Tavily
   [Relevance Agent] Filtered to 5 valid recent articles
   ```
3. If you see errors, check Tavily API key is correct

## Alternative: Local Testing First

If you want to test locally before deploying:

### 1. Create/Update `backend/.env`

```env
# Add to your existing .env file
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxx

# Make sure you also have:
OPENAI_API_KEY=sk-xxxxx
SENDGRID_API_KEY=SG.xxxxx
FROM_EMAIL=ramnathan.au@gmail.com
SECRET_KEY=your-secret-key
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `python-dateutil>=2.8.2` (new dependency).

### 3. Run Locally

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Test Locally

1. Open http://localhost:8000
2. Login or register
3. Generate a test digest
4. Verify articles are recent and URLs are valid
5. Check console logs for filtering messages

### 5. Deploy to Render

Once local testing passes, follow Steps 3-6 from Quick Deployment above.

## Rollback Plan (If Needed)

If something goes wrong:

### Option 1: Revert Environment Variable

1. Go to Render → Environment
2. Remove `TAVILY_API_KEY`
3. Save changes
4. App will restart without Tavily
5. Note: Won't generate fake URLs anymore - will return empty digests

### Option 2: Revert Code

```bash
# Find the previous commit
git log --oneline

# Revert to previous version (replace COMMIT_HASH)
git revert HEAD

# Push revert
git push origin main
```

Render will automatically redeploy the previous version.

## Troubleshooting

### Issue: Deploy Failed

**Error**: `Build failed: requirements.txt`

**Solution**:
```bash
# Make sure requirements.txt is committed
git add backend/requirements.txt
git commit -m "Add python-dateutil to requirements"
git push origin main
```

### Issue: Tavily API Error 401

**Error**: `[Tavily] API error: 401 Unauthorized`

**Solution**:
- API key is invalid or expired
- Go to https://tavily.com/dashboard
- Regenerate API key
- Update in Render environment variables

### Issue: Tavily API Error 429

**Error**: `[Tavily] API error: 429 Too Many Requests`

**Solution**:
- Hit free tier limit (1,000/month)
- Upgrade Tavily plan at https://tavily.com/pricing
- Or wait until next month for quota reset

### Issue: No Articles Found

**Logs**: `[Monitor Agent] Found 0 real articles from Tavily`

**Causes**:
1. Location is too specific (e.g., "123 Main St" instead of "Melbourne")
2. No recent crime news in that location (good news!)
3. Tavily search returned no results

**Solutions**:
- Use broader location (city name, not address)
- Increase `days_back` to 2-3 days in user preferences
- Try different keywords in search

### Issue: Old Articles Still Showing

**Unlikely** - but if it happens:

**Check**:
1. Look at article's published date
2. Check server logs for date filtering messages
3. Verify Tavily returns `published_date` field

**Debug**:
```bash
# In Render logs, search for:
[Relevance Agent] Filtering out old article
```

If not appearing, Tavily might not be returning dates.

## Monitoring

### Key Metrics to Watch

After deployment, monitor these in Render logs:

1. **Article Count**: Should see 3-5 articles per digest
2. **URL Validity**: No `example.com` or `localhost` in logs
3. **Date Filtering**: Should see "Skipping old article" messages
4. **API Errors**: No 401/429 errors from Tavily

### Health Checks

Run daily for first week:
- Generate a digest
- Verify all URLs work
- Check article dates are recent
- Confirm location relevance

## Support

### If You Need Help:

1. **Check Logs**: Render Dashboard → Your Service → Logs
2. **Review Code**: Compare with `IMPROVEMENTS_SUMMARY.md`
3. **Test Locally**: Run local server with debugging
4. **Check API Keys**: Verify all keys in Environment tab

### Useful Links:

- Render Dashboard: https://dashboard.render.com/
- Tavily Dashboard: https://tavily.com/dashboard
- SendGrid Dashboard: https://app.sendgrid.com/
- GitHub Repo: https://github.com/rnathanau/ai-news-agent

## Success Checklist

After deployment, verify:

- [ ] Service shows "Live" status in Render
- [ ] Can login to app successfully
- [ ] Generate digest returns results
- [ ] All article URLs are real (click them!)
- [ ] Article dates are within last 1-2 days
- [ ] Articles mention your configured location
- [ ] Email digests work (if SendGrid configured)
- [ ] No errors in Render logs

## Next Steps

Once deployment is successful:

1. **Test Daily Digests**: Let scheduler run for a few days
2. **Monitor Quality**: Check articles remain relevant
3. **Adjust Preferences**: Fine-tune `days_back`, `radius_km`, etc.
4. **Share Feedback**: Note any issues or improvements needed

---

**Deployment Time**: ~5 minutes (excluding API key signup)
**Difficulty**: Easy
**Risk**: Low (can rollback easily)

Good luck! 🚀


