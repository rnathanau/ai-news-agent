# Arize AX Trace Visualization

## 📊 What Your Traces Look Like in Arize

This document shows you exactly what you'll see in the Arize dashboard when you generate a digest.

---

## 🎯 Complete Trace Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Trace: Digest Generation                                        │
│ Duration: 12.5s                                                  │
│ Status: ✅ Success                                               │
│ Timestamp: 2025-10-21 07:00:00                                  │
│ Project: headsup-news-agent                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 SPAN 1: Monitor Agent                                        │
│ ├─ Type: AGENT                                                  │
│ ├─ Duration: 3.2s                                               │
│ ├─ Tags: ["monitor", "news_search"]                            │
│ └─ Attributes:                                                  │
│    ├─ metadata.agent_type: "monitor"                           │
│    ├─ metadata.location: "Melbourne"                           │
│    ├─ input.value: "Search for crime news in Melbourne"        │
│    └─ output.value: "Found 15 articles"                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─── Child Spans ───┐
                              │                    │
                              ▼                    ▼
        ┌──────────────────────────┐   ┌──────────────────────────┐
        │ TOOL: Tavily Search      │   │ TOOL: Classify Incident  │
        │ Duration: 2.8s           │   │ Duration: 0.4s           │
        │ Input: Query string      │   │ Input: Article text      │
        │ Output: 15 articles      │   │ Output: Classification   │
        └──────────────────────────┘   └──────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ⚖️ SPAN 2: Relevance Agent                                      │
│ ├─ Type: AGENT                                                  │
│ ├─ Duration: 1.5s                                               │
│ ├─ Tags: ["relevance", "ranking"]                              │
│ └─ Attributes:                                                  │
│    ├─ metadata.agent_type: "relevance"                         │
│    ├─ metadata.articles_count: 15                              │
│    ├─ input.value: "15 raw articles"                           │
│    └─ output.value: "5 ranked articles"                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─── Child Spans ───┐
                              │                    │
                              ▼                    ▼
        ┌──────────────────────────┐   ┌──────────────────────────┐
        │ TOOL: Calculate Proximity│   │ TOOL: Severity Score     │
        │ Duration: 0.8s           │   │ Duration: 0.7s           │
        │ Input: Location data     │   │ Input: Article content   │
        │ Output: Distance (km)    │   │ Output: Score (1-10)     │
        └──────────────────────────┘   └──────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 📝 SPAN 3: Summary Agent                                        │
│ ├─ Type: AGENT                                                  │
│ ├─ Duration: 4.8s                                               │
│ ├─ Tags: ["summary", "summarization"]                          │
│ └─ Attributes:                                                  │
│    ├─ metadata.agent_type: "summary"                           │
│    ├─ input.value: "5 articles to summarize"                   │
│    └─ output.value: "5 summaries"                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─── Child Spans (LLM Calls) ───┐
                              │                                 │
                              ▼                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │ LLM: Summarize Article 1                                 │
        │ ├─ Model: gpt-4o-mini                                    │
        │ ├─ Duration: 1.2s                                        │
        │ ├─ Input Tokens: 500                                     │
        │ ├─ Output Tokens: 100                                    │
        │ ├─ Cost: $0.0075                                         │
        │ ├─ Prompt: "Summarize this crime incident..."           │
        │ └─ Response: "A theft occurred at..."                   │
        └──────────────────────────────────────────────────────────┘
                              │
        ┌──────────────────────────────────────────────────────────┐
        │ LLM: Summarize Article 2                                 │
        │ ├─ Model: gpt-4o-mini                                    │
        │ ├─ Duration: 1.5s                                        │
        │ ├─ Input Tokens: 600                                     │
        │ ├─ Output Tokens: 120                                    │
        │ └─ Cost: $0.0090                                         │
        └──────────────────────────────────────────────────────────┘
                              │
        ┌──────────────────────────────────────────────────────────┐
        │ LLM: Summarize Article 3                                 │
        │ ├─ Model: gpt-4o-mini                                    │
        │ ├─ Duration: 1.3s                                        │
        │ ├─ Input Tokens: 550                                     │
        │ ├─ Output Tokens: 110                                    │
        │ └─ Cost: $0.0083                                         │
        └──────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 📧 SPAN 4: Digest Agent                                         │
│ ├─ Type: AGENT                                                  │
│ ├─ Duration: 3.0s                                               │
│ ├─ Tags: ["digest", "synthesis"]                               │
│ └─ Attributes:                                                  │
│    ├─ metadata.agent_type: "digest"                            │
│    ├─ metadata.location: "Melbourne"                           │
│    ├─ input.value: "5 summaries"                               │
│    └─ output.value: "Final digest"                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              └─── Child Span (LLM Call) ───┐
                                                             │
                                                             ▼
        ┌──────────────────────────────────────────────────────────┐
        │ LLM: Synthesize Digest                                   │
        │ ├─ Model: gpt-4o-mini                                    │
        │ ├─ Duration: 2.5s                                        │
        │ ├─ Input Tokens: 1200                                    │
        │ ├─ Output Tokens: 400                                    │
        │ ├─ Cost: $0.0180                                         │
        │ ├─ Prompt: "Create a morning safety briefing..."        │
        │ └─ Response: "# Daily Safety Digest..."                 │
        └──────────────────────────────────────────────────────────┘
```

---

## 📊 Metrics Summary

### Timing Breakdown
```
Total Duration: 12.5s
├─ Monitor Agent:   3.2s (26%)
├─ Relevance Agent: 1.5s (12%)
├─ Summary Agent:   4.8s (38%)
└─ Digest Agent:    3.0s (24%)
```

### Token Usage
```
Total Tokens: 2,580
├─ Summary Agent:  1,980 tokens (77%)
│  ├─ Article 1:    600 tokens
│  ├─ Article 2:    720 tokens
│  └─ Article 3:    660 tokens
└─ Digest Agent:     600 tokens (23%)
   └─ Synthesis:   1,600 tokens
```

### Cost Breakdown
```
Total Cost: $0.0248
├─ Summary Agent:  $0.0248 (77%)
└─ Digest Agent:   $0.0180 (23%)

Daily Cost (100 users): $2.48
Monthly Cost (100 users): $74.40
```

---

## 🔍 Span Attributes Reference

### Monitor Agent
```json
{
  "span.kind": "AGENT",
  "openinference.span.kind": "AGENT",
  "metadata.agent_type": "monitor",
  "metadata.location": "Melbourne",
  "metadata.keywords": "crime theft burglary",
  "metadata.days_back": 1,
  "tags": ["monitor", "news_search"],
  "input.value": "Search for crime news in Melbourne",
  "output.value": "Found 15 potential articles"
}
```

### Relevance Agent
```json
{
  "span.kind": "AGENT",
  "openinference.span.kind": "AGENT",
  "metadata.agent_type": "relevance",
  "metadata.articles_count": 15,
  "metadata.location": "Melbourne",
  "metadata.radius_km": 5,
  "tags": ["relevance", "ranking"],
  "input.value": "15 raw articles",
  "output.value": "5 ranked articles"
}
```

### Summary Agent
```json
{
  "span.kind": "AGENT",
  "openinference.span.kind": "AGENT",
  "metadata.agent_type": "summary",
  "tags": ["summary", "summarization"],
  "input.value": "5 articles to summarize",
  "output.value": "5 summaries generated"
}
```

### Digest Agent
```json
{
  "span.kind": "AGENT",
  "openinference.span.kind": "AGENT",
  "metadata.agent_type": "digest",
  "metadata.location": "Melbourne",
  "tags": ["digest", "synthesis"],
  "input.value": "5 summaries",
  "output.value": "Final digest with 3 articles"
}
```

### LLM Spans (Auto-captured)
```json
{
  "span.kind": "LLM",
  "openinference.span.kind": "LLM",
  "llm.model_name": "gpt-4o-mini",
  "llm.invocation_parameters": "{\"temperature\": 0.7}",
  "llm.input_messages": "[{\"role\": \"system\", \"content\": \"...\"}]",
  "llm.output_messages": "[{\"role\": \"assistant\", \"content\": \"...\"}]",
  "llm.token_count.prompt": 500,
  "llm.token_count.completion": 100,
  "llm.token_count.total": 600
}
```

### Tool Spans (Auto-captured)
```json
{
  "span.kind": "TOOL",
  "openinference.span.kind": "TOOL",
  "tool.name": "search_local_news",
  "tool.description": "Search for recent crime and safety news",
  "input.value": "{\"location\": \"Melbourne\", \"keywords\": \"crime\"}",
  "output.value": "Found 15 articles"
}
```

---

## 🎨 Arize Dashboard Views

### 1. Traces List View
```
┌────────────────────────────────────────────────────────────────┐
│ Traces for: headsup-news-agent                                 │
├────────────────────────────────────────────────────────────────┤
│ Trace ID        │ Status │ Duration │ Timestamp               │
├─────────────────┼────────┼──────────┼─────────────────────────┤
│ abc123...       │   ✅   │  12.5s   │ 2025-10-21 07:00:00    │
│ def456...       │   ✅   │  14.2s   │ 2025-10-21 07:00:05    │
│ ghi789...       │   ❌   │  8.3s    │ 2025-10-21 07:00:10    │
└─────────────────┴────────┴──────────┴─────────────────────────┘
```

### 2. Trace Detail View
```
┌────────────────────────────────────────────────────────────────┐
│ Trace: abc123...                                               │
│ Status: ✅ Success                                              │
│ Duration: 12.5s                                                │
│ Spans: 12                                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Timeline:                                                     │
│  ├─ Monitor Agent     ████████░░░░░░░░░░░░░░░░░░  3.2s       │
│  ├─ Relevance Agent   ░░░░░░░░███░░░░░░░░░░░░░░░  1.5s       │
│  ├─ Summary Agent     ░░░░░░░░░░░████████████░░░  4.8s       │
│  └─ Digest Agent      ░░░░░░░░░░░░░░░░░░░░██████  3.0s       │
│                                                                │
│  Metrics:                                                      │
│  ├─ Total Tokens: 2,580                                       │
│  ├─ Total Cost: $0.0248                                       │
│  └─ LLM Calls: 4                                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 3. Span Detail View
```
┌────────────────────────────────────────────────────────────────┐
│ Span: Summary Agent                                            │
├────────────────────────────────────────────────────────────────┤
│ Type: AGENT                                                    │
│ Duration: 4.8s                                                 │
│ Status: ✅ Success                                              │
│                                                                │
│ Attributes:                                                    │
│ ├─ metadata.agent_type: "summary"                             │
│ ├─ tags: ["summary", "summarization"]                         │
│ └─ input.value: "5 articles to summarize"                     │
│                                                                │
│ Child Spans (3):                                               │
│ ├─ LLM: Summarize Article 1 (1.2s)                            │
│ ├─ LLM: Summarize Article 2 (1.5s)                            │
│ └─ LLM: Summarize Article 3 (1.3s)                            │
│                                                                │
│ Prompt Template:                                               │
│ "You are a news summarization agent. Create concise 2-3       │
│  sentence summaries for each article."                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔎 Example Queries in Arize

### Find All Failed Digests
```
status = ERROR
```

### Find Slow Digests
```
latency > 20000
```

### Find High Token Usage
```
llm.token_count.total > 5000
```

### Find Digests for Melbourne
```
metadata.location = "Melbourne"
```

### Find Digests with Few Articles
```
metadata.articles_count < 5
```

### Find Expensive Digests
```
llm.token_count.total > 3000
```

---

## 📈 Performance Benchmarks

### Target Metrics
```
✅ Total Latency:     < 15s (P95)
✅ Monitor Agent:     < 5s
✅ Relevance Agent:   < 2s
✅ Summary Agent:     < 6s
✅ Digest Agent:      < 4s
✅ Token Usage:       < 3000 tokens
✅ Cost per Digest:   < $0.03
✅ Success Rate:      > 95%
```

### Alert Thresholds
```
⚠️ Latency > 20s
⚠️ Error Rate > 5%
⚠️ Token Usage > 5000
⚠️ Cost > $0.05
```

---

## 🎯 What This Enables

### 1. **Real-Time Monitoring**
- See every digest generation as it happens
- Track success/failure rates
- Monitor performance trends

### 2. **Deep Debugging**
- Click on any failed trace
- See exact error and stack trace
- View all inputs/outputs leading to failure

### 3. **Performance Optimization**
- Identify slowest agents
- Find inefficient LLM calls
- Optimize prompt templates

### 4. **Cost Management**
- Track token usage per digest
- Calculate daily/monthly costs
- Set budget alerts

### 5. **Quality Assurance**
- Monitor article relevance
- Track user satisfaction
- A/B test improvements

---

**This is what you'll see in Arize! 🎉**

For setup instructions, see:
- Quick Start: `ARIZE_QUICK_START.md`
- Full Guide: `ARIZE_SETUP_GUIDE.md`
- Deployment: `ARIZE_RENDER_DEPLOYMENT.md`

