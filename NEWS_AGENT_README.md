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

## Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (or Google Gemini / OpenRouter)
- PostgreSQL (production) or SQLite (development)
- SendGrid API key (for email delivery)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-news-agent.git
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
# - SENDGRID_API_KEY (for emails)
# - FROM_EMAIL (sender email address)
```

4. **Run the server**
```bash
# Development mode with auto-reload
uvicorn main:app --reload --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

5. **Access the application**
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:8000/dashboard.html

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

### Dashboard Features

**Generate New Digest**: Manually create a digest anytime

**View History**: Access past 30 days of digests

**Latest Digest**: See your most recent safety update

### Managing Preferences

Navigate to Settings to update:
- **Location Settings**: Primary location, search radius, severity filter
- **Notification Settings**: Email preferences, delivery time, timezone
- **Account Information**: Name, email (view only)

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

# Email
SENDGRID_API_KEY=SG...
FROM_EMAIL=notifications@youromain.com
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

# Run migrations
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

### Preferences

**Get Preferences**
```http
GET /api/preferences
Authorization: Bearer <token>
```

**Update Preferences**
```http
PUT /api/preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "primary_location": "Melbourne CBD",
  "radius_km": 5,
  "severity_threshold": "medium",
  "email_notifications": true,
  "notification_time": "07:00",
  "timezone": "Australia/Melbourne"
}
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

### Security

- Password hashing with bcrypt
- JWT tokens with 24-hour expiry
- SQL injection prevention via ORM
- XSS prevention in frontend
- HTTPS-only in production

## Deployment

### Local Development

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Production (Render, Railway, etc.)

1. Set environment variables in dashboard
2. Connect GitHub repository
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Docker (Optional)

```bash
docker-compose up --build
```

## Monitoring & Observability

### Arize Integration

Enable tracing by setting:
```env
ARIZE_SPACE_ID=your-space-id
ARIZE_API_KEY=your-api-key
```

View traces at: https://app.arize.com

**Metrics Tracked:**
- Agent execution time
- Tool call success/failure
- LLM token usage
- Error rates
- User engagement

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

### Database Errors

**Problem**: Connection or migration issues

**Solutions**:
- SQLite: Check file permissions
- PostgreSQL: Verify DATABASE_URL format
- Run: `alembic upgrade head` for migrations
- Check database exists and user has permissions

## Extending the System

### Adding New News Sources

1. Create new tool in `main.py`:
```python
@tool
def new_source_search(location: str) -> str:
    """Search custom news source."""
    # Implementation
    return results
```

2. Add tool to monitor_agent's tool list

3. Update search logic to use new source

### Customizing Agents

Each agent can be modified in `main.py`:
- Change prompts for different behavior
- Add/remove tools
- Adjust filtering logic
- Modify output format

### Adding New Features

- **SMS Notifications**: Integrate Twilio
- **Slack Integration**: Post to Slack channels
- **Mobile App**: Build with React Native
- **Real-time Alerts**: Add WebSocket support

## FAQ

**Q: Is this free to use?**
A: The software is free, but you need API keys (OpenAI has paid plans, SendGrid has free tier).

**Q: How accurate are the digests?**
A: Depends on news sources. Real news APIs are most accurate. LLM fallback provides reasonable summaries.

**Q: Can I track multiple locations?**
A: Currently one primary location. Multi-location support coming in v2.

**Q: How is my data used?**
A: Your data stays in your database. We don't share it. LLM providers (OpenAI) have their own data policies.

**Q: Can I self-host?**
A: Yes! Deploy on your own server with full control.

**Q: What about non-English locations?**
A: LLMs support multiple languages. News API coverage varies by region.

## Roadmap

### v1.1 (Current)
- ✅ Multi-agent news curation
- ✅ User authentication
- ✅ Email delivery
- ✅ Historical archive

### v1.2 (Planned)
- [ ] SMS notifications
- [ ] Multi-location tracking
- [ ] Crime trend visualization
- [ ] Mobile app

### v2.0 (Future)
- [ ] Real-time push notifications
- [ ] Social features (share, comment)
- [ ] ML-based personalization
- [ ] Integration with police feeds

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Update documentation
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: https://github.com/yourusername/ai-news-agent/issues
- **Discussions**: https://github.com/yourusername/ai-news-agent/discussions
- **Email**: support@youromain.com

## Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - LLM framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Tailwind CSS](https://tailwindcss.com/) - UI styling
- [SendGrid](https://sendgrid.com/) - Email delivery

Inspired by the need for better local safety awareness tools.

---

**Made with ❤️ for safer neighborhoods**

