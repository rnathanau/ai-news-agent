# Deploy Arize AX Observability to Render

This guide walks you through adding Arize AX observability to your HeadsUp News Agent deployed on Render.

---

## 📋 Prerequisites

Before you begin, make sure you have:
- ✅ Your HeadsUp app deployed on Render: `ai-news-agent-foz7.onrender.com`
- ✅ Access to Render dashboard: https://dashboard.render.com/
- ✅ Arize AX account (or ready to sign up)

---

## 🔑 Step 1: Get Arize Credentials

### Option A: Existing Arize Account

1. Login to Arize: https://app.arize.com/
2. Click your profile icon (top right)
3. Select **"Settings"** or **"API Keys"**
4. Copy your:
   - **Space ID** (format: `space-xxxxx`)
   - **API Key** (format: `arize-xxxxx`)

### Option B: New Arize Account

1. Sign up: https://app.arize.com/signup
2. Complete onboarding
3. Navigate to **Settings → API Keys**
4. Copy your credentials

---

## 🚀 Step 2: Add Environment Variables to Render

### 1. Open Render Dashboard

Go to: https://dashboard.render.com/

### 2. Select Your Service

Click on: **ai-news-agent-foz7** (or your service name)

### 3. Navigate to Environment Tab

Click the **"Environment"** tab in the left sidebar

### 4. Add Arize Variables

Click **"Add Environment Variable"** and add these two:

**Variable 1:**
```
Key:   ARIZE_SPACE_ID
Value: [paste your Space ID here]
```

**Variable 2:**
```
Key:   ARIZE_API_KEY
Value: [paste your API Key here]
```

### 5. Save Changes

Click **"Save Changes"** button at the bottom

---

## ⏳ Step 3: Wait for Deployment

Render will automatically:
1. Detect the environment variable changes
2. Trigger a new deployment
3. Restart your service with Arize enabled

**Expected time**: 2-3 minutes

You'll see:
- Build logs showing "Deploying..."
- Status changes to "Live" when complete

---

## ✅ Step 4: Verify Arize is Working

### 1. Check Render Logs

1. In Render dashboard, click **"Logs"** tab
2. Look for this message:
   ```
   ✅ Arize AX tracing initialized for HeadsUp News Agent
   ```

If you see this, Arize is successfully connected! 🎉

If you see:
```
⚠️ Arize tracing not available: [error message]
```
Double-check your credentials in Step 2.

### 2. Generate a Test Digest

1. Go to your app: https://ai-news-agent-foz7.onrender.com
2. Login to your account
3. Navigate to Dashboard
4. Click **"Generate Digest"**
5. Wait for digest to complete

### 3. View Traces in Arize

1. Go to Arize: https://app.arize.com/
2. You should see a project: **"headsup-news-agent"**
3. Click on the project
4. Click **"Traces"** in the left sidebar
5. You should see your digest generation trace! 🎉

---

## 🔍 What You'll See in Arize

### Trace Visualization

Your digest generation will show as a complete workflow:

```
📊 Digest Generation Trace
├─ 🔍 Monitor Agent (2-5s)
│  ├─ Tavily API Search
│  └─ Article Classification
├─ ⚖️ Relevance Agent (1-2s)
│  ├─ Proximity Calculation
│  └─ Severity Scoring
├─ 📝 Summary Agent (3-5s)
│  └─ LLM Summarization Calls
└─ 📧 Digest Agent (2-4s)
   └─ LLM Synthesis Call
```

### Key Metrics Tracked

For each trace, you'll see:
- **Total Latency**: End-to-end time
- **LLM Token Usage**: Input/output tokens per call
- **Agent Performance**: Time spent in each agent
- **Tool Calls**: Which tools were invoked
- **Errors**: Any failures or exceptions

### Example Insights

**Performance:**
- "Summary Agent taking 8 seconds - optimize prompts?"
- "Monitor Agent found 15 articles but only 3 relevant"

**Quality:**
- "LLM using 5000 tokens per digest - can we reduce?"
- "Relevance Agent filtering out 80% of articles"

**Debugging:**
- "Digest failed at Summary Agent - see error trace"
- "No articles found - check Tavily API key"

---

## 🎯 Next Steps

### 1. Set Up Alerts (Optional)

In Arize, create alerts for:
- Latency > 30 seconds
- Error rate > 5%
- Token usage > 10,000 per digest

### 2. Monitor Daily

Check Arize dashboard daily to:
- Identify performance bottlenecks
- Track token usage and costs
- Debug any failures

### 3. Optimize Based on Data

Use traces to:
- Improve slow agents
- Reduce token consumption
- Enhance article relevance

---

## 🐛 Troubleshooting

### Issue: "Arize tracing not available" in logs

**Cause**: Invalid credentials or missing environment variables

**Solution**:
1. Verify `ARIZE_SPACE_ID` and `ARIZE_API_KEY` are set in Render
2. Check for typos in the values
3. Ensure no extra spaces in the keys/values
4. Re-save and wait for Render to redeploy

### Issue: No traces appearing in Arize

**Cause**: Digest not generated after adding credentials

**Solution**:
1. Ensure Render deployment completed successfully
2. Check logs for "✅ Arize AX tracing initialized"
3. Generate a NEW digest (traces only sent for new digests)
4. Wait 1-2 minutes for traces to appear in Arize

### Issue: Partial traces (missing agents)

**Cause**: Rare - should not happen with current instrumentation

**Solution**:
1. Check Render logs for errors during digest generation
2. Verify all agents completed successfully
3. Contact support if issue persists

### Issue: Wrong project name in Arize

**Cause**: Old code with different project name

**Solution**:
Already fixed! The code now uses `"headsup-news-agent"` as the project name.

---

## 📊 Environment Variables Summary

After setup, your Render environment should have:

```env
# LLM
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://...

# Security
SECRET_KEY=...

# Email
SENDGRID_API_KEY=SG...
FROM_EMAIL=notifications@headsup.to
APP_DOMAIN=https://ai-news-agent-foz7.onrender.com

# News API
TAVILY_API_KEY=tvly-...

# Observability (NEW!)
ARIZE_SPACE_ID=space-xxxxx
ARIZE_API_KEY=arize-xxxxx
```

---

## 🎓 Learning Resources

- **Arize Docs**: https://docs.arize.com/
- **OpenInference Spec**: https://github.com/Arize-ai/openinference
- **LangChain Tracing**: https://docs.arize.com/phoenix/tracing/integrations-tracing/langchain
- **Detailed Setup Guide**: See [ARIZE_SETUP_GUIDE.md](ARIZE_SETUP_GUIDE.md)

---

## ✅ Verification Checklist

Before you're done, verify:

- [ ] Arize credentials added to Render environment
- [ ] Render service redeployed successfully
- [ ] Logs show "✅ Arize AX tracing initialized"
- [ ] Generated a test digest after deployment
- [ ] Logged into Arize dashboard
- [ ] Found "headsup-news-agent" project
- [ ] Viewed trace for test digest
- [ ] All 4 agents visible in trace
- [ ] LLM calls showing prompts and responses

---

## 🎉 Success!

You now have complete observability of your HeadsUp News Agent!

**What you can do now:**
- 🔍 Debug issues 10x faster
- 📊 Optimize agent performance
- 💰 Monitor and reduce costs
- 📈 Track quality metrics
- 🚀 Improve user experience

---

**Last Updated**: October 21, 2025  
**Service**: ai-news-agent-foz7.onrender.com  
**Tracing**: Arize AX

