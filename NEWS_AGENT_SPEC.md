# AI News Agent - Technical Specification

## Overview

The AI News Agent is a personalized safety news digest system that automatically monitors, curates, and delivers crime/safety news for user-specified neighborhoods. Built on a multi-agent architecture using LangGraph, it demonstrates production-ready AI engineering patterns.

## System Architecture

### Multi-Agent Workflow

```
User Request (location, preferences)
           |
           v
    [Monitor Agent] ────> Search crime/safety news
           |
           v
    [Relevance Agent] ──> Filter by proximity & severity
           |
           v
    [Summary Agent] ────> Generate concise summaries
           |
           v
    [Digest Agent] ─────> Synthesize final briefing
           |
           v
    Database + Email Delivery
```

### Technology Stack

- **Backend**: FastAPI, Python 3.10+
- **AI Framework**: LangGraph, LangChain
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: JWT with bcrypt password hashing
- **Email**: SendGrid
- **Scheduler**: APScheduler
- **Frontend**: HTML, TailwindCSS, Vanilla JavaScript
- **LLM**: OpenAI GPT-4o-mini (default), Google Gemini (alternative)
- **Observability**: Arize/OpenInference (optional)

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### User Preferences Table
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE REFERENCES users(id),
    primary_location VARCHAR(500),
    additional_locations JSON,
    email_notifications BOOLEAN DEFAULT TRUE,
    notification_time VARCHAR(5) DEFAULT '07:00',
    timezone VARCHAR(50) DEFAULT 'UTC',
    severity_threshold VARCHAR(20) DEFAULT 'all',
    radius_km INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

### News Digests Table
```sql
CREATE TABLE news_digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    location VARCHAR(500) NOT NULL,
    digest_date TIMESTAMP NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    articles JSON NOT NULL,
    summary_text TEXT,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    email_opened BOOLEAN DEFAULT FALSE
);
```

### News Articles Table (Cache)
```sql
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) UNIQUE NOT NULL,
    source VARCHAR(255),
    published_at TIMESTAMP,
    content TEXT,
    summary TEXT,
    location VARCHAR(500),
    incident_type VARCHAR(100),
    severity_score INTEGER,
    latitude VARCHAR(50),
    longitude VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## News Agent System

### Monitor Agent

**Purpose**: Searches for recent crime/safety news in the specified location.

**Tools**:
- `search_local_news(location, keywords, days_back)` - Web search for news
- `classify_incident_type(article_text)` - Categorize incident type

**Output**: List of raw articles with title, content, source, URL

### Relevance Agent

**Purpose**: Filters and ranks articles by proximity, severity, and recency.

**Tools**:
- `calculate_proximity(incident_location, user_location)` - Distance estimation
- `severity_score(article_text, incident_type)` - Severity assessment
- `extract_location_details(article_text)` - Parse addresses/neighborhoods

**Output**: Top 3-5 ranked articles most relevant to the user

### Summary Agent

**Purpose**: Generates concise 2-3 sentence summaries for each article.

**Tools**:
- `summarize_article(article_text, title)` - Generate summary

**Output**: Articles with generated summaries

### Digest Agent

**Purpose**: Synthesizes top 3 articles into a cohesive morning briefing.

**Tools**: None (uses LLM directly)

**Output**: Final formatted digest with:
- Brief overview
- Top 3 incidents with details
- Safety recommendations

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### User Management

- `GET /api/users/me` - Get user profile
- `PUT /api/users/me` - Update user profile

### Preferences

- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update preferences (location, notifications, etc.)

### Digests

- `POST /api/digests/generate` - Generate new digest
- `GET /api/digests` - List user's digest history
- `GET /api/digests/{id}` - Get specific digest
- `GET /api/digests/latest` - Get most recent digest

### Health

- `GET /health` - Service health check

## Authentication Flow

1. User registers with email/password
2. Password hashed with bcrypt
3. JWT token generated with 24-hour expiry
4. Token included in Authorization header: `Bearer <token>`
5. Protected endpoints verify token and extract user ID

## Daily Digest Generation Flow

### Automated (via Scheduler)

1. Scheduler runs hourly (checks timezone matching)
2. For each active user with email notifications:
   - Check if current time matches user's preferred notification time
   - Get user preferences (location, severity threshold, radius)
   - Generate digest using news agent workflow
   - Save digest to database
   - Send email if email notifications enabled
3. Mark digest as sent with timestamp

### Manual (via API)

1. User clicks "Generate Digest" in dashboard
2. API endpoint `/api/digests/generate` invoked
3. News agent workflow executes
4. Digest saved and displayed to user
5. Email optionally sent based on preferences

## Email System

### Template Structure

- HTML email with responsive design
- Header with date and location
- Brief overview section
- Up to 3 article summaries with links
- Footer with preferences and unsubscribe links
- Styled for readability across email clients

### Delivery

- SendGrid API integration
- Graceful fallback if API key not configured
- Email tracking (sent status, timestamp)
- Future: Open tracking, click tracking

## Scheduler Configuration

### Environment Variables

- `ENABLE_SCHEDULER` - Enable/disable automated generation (default: 1)
- `DIGEST_GENERATION_TIME` - Base generation time in UTC (default: "00:00")

### Behavior

- Runs hourly to accommodate different timezones
- Each execution checks which users should receive digests based on:
  - User's timezone
  - User's preferred notification time
  - Within 1-hour window tolerance
- Batch processes users to avoid rate limits

## News Source Integration

### Hybrid Approach

1. **Primary**: Real news APIs
   - Tavily API (AI-optimized search)
   - News API (comprehensive news aggregation)
   - SerpAPI (fallback)

2. **Fallback**: LLM generation
   - When no API keys configured
   - When API rate limits exceeded
   - Generates realistic summaries based on typical patterns

### Tool Implementation

All tools follow this pattern:
```python
@tool
def tool_name(params) -> str:
    # Try real API
    result = _search_api(query)
    if result:
        return result
    
    # LLM fallback
    return _llm_fallback(instruction, context)
```

## Security Considerations

### Authentication

- Passwords hashed with bcrypt (cost factor: 12)
- JWT tokens with 24-hour expiry
- SECRET_KEY must be changed in production
- HTTPS enforced in production

### Authorization

- All digest endpoints require valid JWT
- Users can only access their own digests
- Profile/preference endpoints user-scoped

### Input Validation

- Pydantic schemas validate all inputs
- SQL injection prevented via SQLAlchemy ORM
- XSS prevention in frontend (sanitized markdown rendering)

### Rate Limiting

- Consider implementing per-user rate limits
- Prevent abuse of digest generation endpoint
- Email sending rate limits via SendGrid

## Observability

### Arize Integration

- Agent execution tracing
- Tool call tracking
- LLM prompt/response logging
- Performance metrics
- Error tracking

### Metrics to Monitor

- Digest generation time
- Email delivery success rate
- User engagement (digest opens, clicks)
- Agent failure rates
- API quota usage

## Deployment

### Prerequisites

- Python 3.10+
- PostgreSQL database
- OpenAI API key (or Google/OpenRouter)
- SendGrid API key (for email)
- Domain for production deployment

### Environment Setup

1. Copy `backend/env.example` to `backend/.env`
2. Configure required variables:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `OPENAI_API_KEY`
   - `SENDGRID_API_KEY`
   - `FROM_EMAIL`

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Initialize database:
```bash
# PostgreSQL
alembic upgrade head

# SQLite (auto-initialized)
python main.py
```

5. Run server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Production Deployment

- Use PostgreSQL (not SQLite)
- Set strong SECRET_KEY (32+ random characters)
- Enable HTTPS/TLS
- Use production-grade WSGI server (gunicorn)
- Set up monitoring and logging
- Configure backup strategy for database
- Use environment variables (not .env file)

## Development Workflow

### Local Setup

1. Clone repository
2. Set up virtual environment
3. Install dependencies
4. Configure `.env` with dev credentials
5. Run with `uvicorn --reload` for hot reloading

### Testing

Manual testing endpoints:
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234"}'

# Generate digest (with token)
curl -X POST http://localhost:8000/api/digests/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Database Migrations

Using Alembic for schema changes:
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Performance Optimization

### Agent Execution

- Sequential flow prevents unnecessary parallel API calls
- Tool results cached within single digest generation
- Timeouts on search API calls (10 seconds)

### Database

- Indexes on frequently queried fields:
  - users.email
  - news_digests.user_id
  - news_digests.digest_date
  - news_articles.url

### Caching Strategy

- Consider Redis for:
  - Recent digests (avoid regeneration)
  - News article deduplication
  - User preference caching

## Future Enhancements

### Phase 2 Features

- Real-time push notifications (WebSocket)
- Mobile app (React Native)
- Social features (share digests, comment)
- Crime trend visualization
- Multi-location tracking
- Customizable severity filters
- Integration with police department feeds

### Advanced Features

- ML-based personalization (learn preferences)
- Geofencing and proximity alerts
- Integration with home security systems
- Community safety scores
- Predictive analytics (crime patterns)
- Voice assistant integration

## Troubleshooting

### Common Issues

**Digest generation fails**:
- Check LLM API key is valid
- Verify user has location configured
- Check API rate limits
- Review Arize traces for errors

**Email not received**:
- Verify SendGrid API key
- Check email_notifications preference
- Look for email in spam folder
- Check SendGrid dashboard for delivery status

**Database connection errors**:
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Verify database exists
- Check user permissions

**Scheduler not running**:
- Check ENABLE_SCHEDULER=1
- Verify no startup errors in logs
- Test manual digest generation first
- Check timezone configuration

## Contributing

### Code Style

- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Write tests for new features
- Update this spec for architectural changes

### Pull Request Process

1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Update documentation
5. Submit PR with clear description

## License

[Specify license]

## Contact

[Specify contact information]

