# AI News Agent - Personalized Safety Digests

> Stay informed about crime and safety incidents in your neighborhood with AI-powered daily digests.

## What Is This?

AI News Agent is a multi-agent AI system that monitors local crime and safety news, curates the most relevant incidents for your specific neighborhood, and delivers a personalized daily digest via email and web dashboard.

**Key Features:**
- 🤖 **Multi-Agent AI**: Four specialized agents working in parallel
- 📍 **Hyper-Local**: Configure exact neighborhood and search radius
- 📧 **Daily Email Digests**: Automated delivery at your preferred time
- 🌍 **Global Support**: Any city/neighborhood worldwide
- 📊 **Historical Archive**: View past 30 days of digests
- 🔒 **Secure & Private**: User authentication with encrypted passwords

## How It Works

### The Four-Agent System

```
┌──────────────────┐
│  Monitor Agent   │  Searches for crime/safety news in your location
└────────┬─────────┘
         │
         v
┌──────────────────┐
│ Relevance Agent  │  Filters by proximity, severity, and recency
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Summary Agent   │  Generates concise 2-3 sentence summaries
└────────┬─────────┘
         │
         v
┌──────────────────┐
│  Digest Agent    │  Synthesizes top 3 into cohesive briefing
└──────────────────┘
```

### Example Workflow

1. **You configure** your location: "Melbourne CBD, Australia"
2. **Monitor Agent** searches news APIs for recent crime/safety incidents
3. **Relevance Agent** filters incidents within 5km and ranks by severity
4. **Summary Agent** creates clear, concise summaries of each incident
5. **Digest Agent** synthesizes the top 3 into your morning briefing
6. **Email sent** to your inbox at 7:00 AM local time

## Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (or Google Gemini / OpenRouter)
- PostgreSQL (production) or SQLite (development)
- SendGrid API key (optional - for email delivery)
- Arize AX credentials (optional - for observability & tracing)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/rnathanau/ai-news-agent.git
cd ai-news-agent
```

2. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Copy example config
cp env.example .env

# Edit .env with your credentials
# Minimum required:
# - OPENAI_API_KEY or GOOGLE_API_KEY
# - DATABASE_URL (defaults to SQLite if not set)
# - SECRET_KEY (for JWT tokens)
# - SENDGRID_API_KEY (optional - for emails)
# - FROM_EMAIL (sender email address)
# - ARIZE_SPACE_ID (optional - for observability)
# - ARIZE_API_KEY (optional - for observability)
```

4. **Run the server**
```bash
# Development mode with auto-reload
cd backend
python -m uvicorn main:app --reload --port 8000

# Production mode
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

5. **Access the application**
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/dashboard.html

## Usage Guide

### First Time Setup

1. **Register an account** at `/auth.html`
   - Provide email and password (min 8 characters)
   - Optionally add your name

2. **Set your location** in Settings (`/profile.html`)
   - Enter your primary location (e.g., "Brooklyn, NY")
   - Configure search radius (1-20 km)
   - Set severity filter (all/medium/high)

3. **Configure notifications**
   - Enable/disable email notifications
   - Set preferred delivery time
   - Choose your timezone

4. **Generate your first digest**
   - Click "Generate Digest" on dashboard
   - View results immediately
   - Digests auto-generate daily

## Configuration

### Environment Variables

#### Required

```env
# LLM Provider (choose one)
OPENAI_API_KEY=sk-...
# OR
GOOGLE_API_KEY=...
# OR
OPENROUTER_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/newsagent

# Security
SECRET_KEY=your-secret-key-min-32-characters

# Email (optional for testing, required for email notifications)
SENDGRID_API_KEY=SG...
FROM_EMAIL=notifications@yourdomain.com
```

#### Optional

```env
# News APIs (for real-time data)
TAVILY_API_KEY=...
NEWS_API_KEY=...
SERPAPI_API_KEY=...

# Observability
ARIZE_SPACE_ID=...
ARIZE_API_KEY=...

# Scheduler
ENABLE_SCHEDULER=1
DIGEST_GENERATION_TIME=00:00
```

### Database Setup

#### SQLite (Development)
```bash
# Automatic - no setup needed
# Database created at ./news_agent.db
```

#### PostgreSQL (Production)
```bash
# Create database
createdb newsagent

# Run migrations (if needed)
alembic upgrade head
```

## API Reference

### Authentication

**Register**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response: { "access_token": "...", "token_type": "bearer" }
```

### Digests 

**Generate Digest**
```http
POST /api/digests/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "location": "Brooklyn, NY"  // Optional, uses user's primary location
}
```

**List Digests**
```http
GET /api/digests?skip=0&limit=30
Authorization: Bearer <token>
```

**Get Latest Digest**
```http
GET /api/digests/latest
Authorization: Bearer <token>
```

## Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.10+)
- **AI**: LangGraph, LangChain, OpenAI GPT-4o-mini
- **Database**: PostgreSQL / SQLite
- **Auth**: JWT with bcrypt
- **Email**: SendGrid
- **Frontend**: HTML, TailwindCSS, Vanilla JS
- **Scheduler**: APScheduler

### Design Patterns

- **Multi-Agent Orchestration**: LangGraph for workflow management
- **Graceful Degradation**: Works without optional APIs (uses LLM fallback)
- **Hybrid Data Sources**: Real APIs + LLM generation
- **Tool-Augmented Agents**: Structured tools for data retrieval
- **Stateful Graph**: Shared state across agent pipeline

## Deployment

### Render (Recommended)

1. Fork this repository
2. Create new Web Service on Render
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Set environment variables in Render dashboard:
   - `OPENAI_API_KEY`
   - `SECRET_KEY`
   - `SENDGRID_API_KEY` (optional)
   - `FROM_EMAIL` (optional)
6. Deploy!

### Manual Deployment

```bash
# Production
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Troubleshooting

### Digest Generation Fails

**Problem**: Error when clicking "Generate Digest"

**Solutions**:
1. Verify LLM API key is valid
2. Check you have a location configured
3. Check API rate limits
4. View detailed errors in browser console

### Email Not Received

**Problem**: Digest generated but email not delivered

**Solutions**:
1. Check SendGrid API key is configured
2. Verify email_notifications is enabled in preferences
3. Check spam/junk folder
4. View SendGrid dashboard for delivery status

### Scheduler Not Running

**Problem**: No automated daily digests

**Solutions**:
1. Verify `ENABLE_SCHEDULER=1` in .env
2. Check server logs for startup errors
3. Test manual digest generation first
4. Verify timezone configuration

## Observability with Arize AX

Your HeadsUp News Agent comes with built-in observability using Arize AX. This allows you to:

- 🔍 **Visualize Agent Workflows**: See the complete execution flow of all 4 agents
- 📊 **Track LLM Performance**: Monitor token usage, latency, and costs
- 🐛 **Debug Issues**: View exact prompts, responses, and errors
- 📈 **Analyze Patterns**: Understand which agents are slowest, which tools are most used

### Quick Setup

1. **Sign up for Arize**: https://app.arize.com/signup
2. **Get your credentials** from Settings → API Keys
3. **Add to environment variables**:
   ```env
   ARIZE_SPACE_ID=your-space-id
   ARIZE_API_KEY=your-api-key
   ```
4. **Restart your server** and generate a digest
5. **View traces** at https://app.arize.com/ under project "headsup-news-agent"

### What Gets Traced

Every digest generation creates a complete trace showing:
- **Monitor Agent**: Search queries, API calls, articles found
- **Relevance Agent**: Filtering logic, proximity calculations
- **Summary Agent**: LLM calls for summarization
- **Digest Agent**: Final synthesis and formatting

For detailed setup instructions, see [ARIZE_SETUP_GUIDE.md](ARIZE_SETUP_GUIDE.md)

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/rnathanau/ai-news-agent/issues
- **Documentation**: See NEWS_AGENT_README.md for detailed documentation

## Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - UI styling
- [SendGrid](https://sendgrid.com/) - Email delivery

---

**Made for safer neighborhoods**
