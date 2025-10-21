# Arize AX Observability Setup Guide

## Overview

Your HeadsUp News Agent is now instrumented with Arize AX for complete observability of your multi-agent system. You can visualize the entire agent workflow, LLM calls, and tool usage in the Arize dashboard.

---

## ✅ What's Already Configured

Your application already has:
- ✅ `arize-otel>=0.8.1` installed
- ✅ `openinference-instrumentation-langchain>=0.1.19` installed
- ✅ `openinference-instrumentation-litellm>=0.1.0` installed
- ✅ Auto-instrumentation for LangChain agents, chains, and tools
- ✅ Auto-instrumentation for LLM calls (OpenAI, Google Gemini, etc.)
- ✅ Proper span attributes for Monitor, Relevance, Summary, and Digest agents

---

## 🔑 Get Your Arize Credentials

### 1. Sign Up for Arize (if you haven't)

Visit: **https://app.arize.com/signup**

### 2. Get Your Space ID and API Key

1. Login to Arize: https://app.arize.com/
2. Click on your profile (top right)
3. Go to **"API Keys"** or **"Settings"**
4. Copy your:
   - **Space ID** (looks like: `space-xxxxx`)
   - **API Key** (looks like: `arize-xxxxx`)

---

## 🚀 Configure Environment Variables

### For Render (Production):

1. Go to: https://dashboard.render.com/
2. Click on your service: **ai-news-agent-foz7**
3. Click **"Environment"** tab
4. Add these two variables:

```
ARIZE_SPACE_ID=your-space-id-here
ARIZE_API_KEY=your-api-key-here
```

5. Click **"Save Changes"**
6. Render will restart automatically (2-3 minutes)

### For Local Development:

Add to `backend/.env`:

```env
# Arize AX Observability
ARIZE_SPACE_ID=your-space-id-here
ARIZE_API_KEY=your-api-key-here
```

---

## 📊 What Gets Traced

### Agent Workflow Visualization

Your multi-agent system will be fully traced:

```
User Request
    ↓
Monitor Agent (AGENT span)
    ├─ search_local_news (TOOL span)
    ├─ classify_incident_type (TOOL span)
    └─ Tavily API call (traced)
    ↓
Relevance Agent (AGENT span)
    ├─ calculate_proximity (TOOL span)
    ├─ severity_score (TOOL span)
    └─ extract_location_details (TOOL span)
    ↓
Summary Agent (AGENT span)
    └─ LLM call for summarization (LLM span)
    ↓
Digest Agent (AGENT span)
    └─ LLM call for synthesis (LLM span)
    ↓
Final Digest Returned
```

### Span Attributes Captured

For each span, Arize captures:
- **Agent Type**: monitor, relevance, summary, digest
- **Location**: User's configured location
- **Keywords**: Search keywords used
- **Articles Count**: Number of articles processed
- **LLM Model**: Which model was used (gpt-4o-mini, gemini-pro, etc.)
- **Prompt Template**: The actual prompts used
- **Input/Output**: Request and response data
- **Latency**: Time taken for each step
- **Token Usage**: LLM token consumption

---

## 🔍 View Traces in Arize

### 1. Generate a Digest

1. Go to your app: https://ai-news-agent-foz7.onrender.com
2. Login
3. Generate a digest (Dashboard → "Generate Digest")

### 2. View in Arize Dashboard

1. Go to: https://app.arize.com/
2. Select project: **"headsup-news-agent"**
3. Click **"Traces"** in the left sidebar
4. You'll see your agent workflow visualized!

### 3. What You'll See

**Trace View:**
- Complete agent pipeline visualization
- Each agent as a separate span
- Tool calls nested under agents
- LLM calls with prompts and responses
- Timing information for each step

**Metrics:**
- Total latency
- LLM token usage
- Success/error rates
- Agent performance

**Debugging:**
- See exact prompts sent to LLMs
- View tool inputs/outputs
- Identify bottlenecks
- Track errors and exceptions

---

## 🎯 Key Features

### 1. Agent Performance Monitoring

See which agent takes the longest:
- Monitor Agent: Typically 2-5 seconds (Tavily API call)
- Relevance Agent: Typically 1-2 seconds (filtering)
- Summary Agent: Typically 3-5 seconds (LLM calls)
- Digest Agent: Typically 2-4 seconds (LLM synthesis)

### 2. LLM Call Tracking

Track every LLM call:
- Model used (gpt-4o-mini, gemini-pro, etc.)
- Prompt sent
- Response received
- Tokens consumed
- Latency

### 3. Tool Usage Analytics

See how often each tool is called:
- `search_local_news`: Once per digest
- `calculate_proximity`: Multiple times per digest
- `severity_score`: Once per article
- `extract_location_details`: As needed

### 4. Error Tracking

Automatically captures:
- Failed API calls
- LLM errors
- Tool failures
- Exception stack traces

---

## 📈 Example Queries in Arize

### Find Slow Digests:
```
latency > 15000ms
```

### Find Failed Digests:
```
status = ERROR
```

### Find Digests for Specific Location:
```
metadata.location = "Melbourne"
```

### Find High Token Usage:
```
llm.token_count.total > 5000
```

---

## 🔧 Advanced Configuration

### Custom Span Attributes

The code already adds custom attributes for better observability:

```python
# In monitor_agent
current_span.set_attribute("metadata.agent_type", "monitor")
current_span.set_attribute("metadata.location", location)

# In relevance_agent
current_span.set_attribute("metadata.agent_type", "relevance")
current_span.set_attribute("metadata.articles_count", len(raw_articles))
```

### Session and User Tracking

Already implemented with `using_attributes`:

```python
with using_attributes(tags=["monitor", "news_search"]):
    # Agent execution
```

---

## 🐛 Troubleshooting

### Issue: No Traces Appearing

**Check:**
1. Environment variables are set correctly
2. Render service has restarted
3. You've generated a digest after adding credentials
4. Check Render logs for "✅ Arize AX tracing initialized"

**Solution:**
```bash
# Check Render logs
# Should see: "✅ Arize AX tracing initialized for HeadsUp News Agent"
# If not, check environment variables
```

### Issue: "Tracing not available" Warning

**Cause:** Arize credentials not set

**Solution:**
1. Add `ARIZE_SPACE_ID` and `ARIZE_API_KEY` to Render
2. Restart service
3. Generate a new digest

### Issue: Partial Traces

**Cause:** Some agents not being traced

**Solution:**
Already fixed! All agents (Monitor, Relevance, Summary, Digest) are instrumented with proper span attributes.

---

## 📊 Metrics to Monitor

### Performance Metrics:
- **P50 Latency**: Should be < 10 seconds
- **P95 Latency**: Should be < 20 seconds
- **P99 Latency**: Should be < 30 seconds

### Quality Metrics:
- **Success Rate**: Should be > 95%
- **Articles Found**: Average 3-5 per digest
- **Token Usage**: Average 2000-4000 tokens per digest

### Cost Metrics:
- **LLM Costs**: Track token usage per digest
- **API Costs**: Monitor Tavily API calls

---

## 🎓 Best Practices

### 1. Regular Monitoring

Check Arize dashboard daily for:
- Error spikes
- Latency increases
- Token usage trends

### 2. Set Up Alerts

In Arize, create alerts for:
- Latency > 30 seconds
- Error rate > 5%
- Token usage > 10,000 per digest

### 3. Analyze Patterns

Look for:
- Which locations have most incidents
- Which times of day have most activity
- Which agents are slowest

### 4. Optimize Based on Data

Use traces to:
- Identify slow LLM calls
- Optimize prompts
- Reduce unnecessary tool calls
- Improve caching

---

## 🔗 Useful Links

- **Arize Dashboard**: https://app.arize.com/
- **Arize Docs**: https://docs.arize.com/
- **OpenInference Spec**: https://github.com/Arize-ai/openinference
- **LangChain Instrumentation**: https://docs.arize.com/phoenix/tracing/integrations-tracing/langchain

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Environment variables added to Render
- [ ] Render service restarted
- [ ] Generated a test digest
- [ ] Checked Render logs for "✅ Arize AX tracing initialized"
- [ ] Logged into Arize dashboard
- [ ] Selected "headsup-news-agent" project
- [ ] Viewed traces in Traces tab
- [ ] See complete agent workflow
- [ ] All 4 agents visible (Monitor, Relevance, Summary, Digest)
- [ ] LLM calls traced with prompts
- [ ] Tool calls visible

---

## 🎉 Success!

Once you see traces in Arize, you have complete observability of your HeadsUp News Agent!

You can now:
- ✅ Debug issues faster
- ✅ Optimize performance
- ✅ Monitor costs
- ✅ Improve user experience
- ✅ Track agent behavior

---

**Last Updated**: October 21, 2025
**Project**: HeadsUp News Agent
**Tracing**: Arize AX

