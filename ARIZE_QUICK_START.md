# Arize AX - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Get Credentials (2 minutes)
1. Go to: https://app.arize.com/signup
2. Sign up (or login if you have an account)
3. Navigate to: **Settings → API Keys**
4. Copy:
   - `ARIZE_SPACE_ID` (looks like: `space-xxxxx`)
   - `ARIZE_API_KEY` (looks like: `arize-xxxxx`)

### Step 2: Add to Render (2 minutes)
1. Go to: https://dashboard.render.com/
2. Click: **ai-news-agent-foz7**
3. Click: **Environment** tab
4. Click: **Add Environment Variable**
5. Add both:
   ```
   ARIZE_SPACE_ID = [paste your space ID]
   ARIZE_API_KEY = [paste your API key]
   ```
6. Click: **Save Changes**
7. Wait 2-3 minutes for deployment

### Step 3: Test (1 minute)
1. Check Render logs for: `✅ Arize AX tracing initialized`
2. Go to: https://ai-news-agent-foz7.onrender.com
3. Generate a digest
4. Go to: https://app.arize.com/
5. Click project: **headsup-news-agent**
6. Click: **Traces**
7. See your trace! 🎉

---

## 📊 What You'll See

### Trace View
```
Digest Generation (12.5s)
├─ Monitor Agent (3.2s)
│  └─ Tavily Search: 15 articles
├─ Relevance Agent (1.5s)
│  └─ Filtered to 5 articles
├─ Summary Agent (4.8s)
│  └─ 3 LLM calls
└─ Digest Agent (3.0s)
   └─ 1 LLM call
```

### Key Metrics
- **Total Time**: 12.5 seconds
- **LLM Tokens**: 2,500 tokens
- **Cost**: $0.02
- **Articles Found**: 15
- **Articles Sent**: 3

---

## 🔍 Common Use Cases

### Debug a Failed Digest
1. Go to Arize → Traces
2. Filter by: `status = ERROR`
3. Click the failed trace
4. See which agent failed and why

### Find Slow Digests
1. Go to Arize → Traces
2. Filter by: `latency > 20000ms`
3. Click a slow trace
4. See which agent is taking longest

### Monitor Token Usage
1. Go to Arize → Traces
2. View: `llm.token_count.total`
3. Track average per digest
4. Set alerts for high usage

### Track Costs
1. Go to Arize → Traces
2. View token usage per trace
3. Calculate: tokens × $0.000015 (GPT-4o-mini)
4. Monitor daily/monthly costs

---

## 📚 Full Documentation

- **Complete Setup**: See `ARIZE_SETUP_GUIDE.md`
- **Render Deployment**: See `ARIZE_RENDER_DEPLOYMENT.md`
- **Implementation Details**: See `ARIZE_IMPLEMENTATION_SUMMARY.md`
- **Test Script**: Run `python test_arize_tracing.py`

---

## 🆘 Quick Troubleshooting

### No traces appearing?
1. Check Render logs for "✅ Arize AX tracing initialized"
2. Generate a NEW digest (after adding credentials)
3. Wait 1-2 minutes
4. Refresh Arize dashboard

### Wrong project name?
Already fixed! Now uses `headsup-news-agent`

### Partial traces?
All 4 agents are instrumented, should see complete traces

### Need help?
- Arize Docs: https://docs.arize.com/
- Arize Support: support@arize.com

---

**That's it! You now have complete observability of your AI News Agent! 🎉**

