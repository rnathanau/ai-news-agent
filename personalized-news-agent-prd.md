# Personalized News Agent - Product Requirements Document & Implementation Plan

## Product Requirements Document

### Problem Statement

Residents need timely awareness of local safety incidents (theft, home intrusion, crime) in their neighborhood but face information overload from multiple news sources, social media, and police reports. Current solutions require manual monitoring of various channels, leading to missed important updates or wasted time.

### Product Vision

A personalized AI-powered news agent that automatically monitors, curates, and delivers the top 3 most relevant local safety/crime articles for any specified neighborhood each morning via email and web dashboard.

### Target Users

- **Primary**: Homeowners and renters in urban/suburban neighborhoods concerned about local safety
- **Secondary**: Real estate agents, neighborhood watch coordinators, property managers

### Core Features

#### 1. Geographic Configuration (MVP)

- User enters specific location (e.g., "Melbourne CBD", "Brooklyn, NY", "Mission District, San Francisco")
- Supports any city/neighborhood globally
- Location stored per user profile

#### 2. Multi-Agent News Intelligence

- **Monitor Agent**: Scans news APIs, police feeds, local news sites for crime/safety incidents
- **Relevance Agent**: Filters and ranks articles by proximity, severity, and recency
- **Summary Agent**: Generates concise 2-3 sentence summaries with key facts
- **Digest Agent**: Synthesizes top 3 articles into a coherent morning briefing

#### 3. Daily Delivery Mechanisms

- **Web Dashboard**: Clean UI showing latest digest, historical digests, and trend analysis
- **Email Subscription**: Optional daily digest sent at user-configured time (default: 7 AM local)

#### 4. User Authentication & Personalization

- User registration with email/password
- Profile management: location, delivery preferences, notification time
- Multiple location tracking (e.g., home + vacation property)

#### 5. News Source Integration (Hybrid Approach)

- **Primary**: Real news APIs (News API, Tavily, SerpAPI) for current events
- **Fallback**: LLM-generated summaries when APIs unavailable/rate-limited
- **Source attribution**: Each article shows original source and publication date

### Success Metrics

- **User Engagement**: 70%+ of users open email digest within 24 hours
- **Retention**: 60%+ weekly active users after 30 days
- **Accuracy**: 90%+ of flagged incidents are within specified neighborhood radius
- **Response Time**: Digest generation completes in <30 seconds
- **User Satisfaction**: NPS score >40

### Non-Goals (v1)

- Real-time push notifications (planned for v2)
- Social features (commenting, sharing)
- Mobile native app (web-responsive is sufficient)
- Historical crime data visualization beyond 30 days

### Technical Architecture (High-Level)

- **Backend**: Python FastAPI, LangGraph multi-agent orchestration
- **Frontend**: HTML/TailwindCSS responsive web app
- **Database**: PostgreSQL for users, SQLite for digests/cache
- **Auth**: JWT-based authentication
- **Deployment**: Render/Railway with scheduled daily jobs
- **Observability**: Arize for agent tracing and debugging

---

## Implementation Summary

All 5 phases have been completed successfully:

✅ **Phase 1**: Database, authentication, and user management
✅ **Phase 2**: Four-agent news curation system
✅ **Phase 3**: Web dashboard and email delivery
✅ **Phase 4**: Automated daily digest scheduling
✅ **Phase 5**: Observability, documentation, and polish

### What Was Built

- **21+ new files** including backend services, frontend pages, and documentation
- **4 specialized AI agents**: monitor, relevance, summary, digest
- **Complete authentication system** with JWT and bcrypt
- **Modern web interface** with TailwindCSS
- **Email delivery system** with HTML templates
- **Automated scheduler** for daily digests
- **Comprehensive documentation**: README, Technical Spec, Implementation Summary

### Key Architecture Decisions

1. **Sequential agent flow** (monitor → relevance → summary → digest)
2. **Hybrid news sources** (Real APIs with LLM fallback)
3. **PostgreSQL/SQLite** for flexible deployment
4. **Timezone-aware scheduling** for global user support
5. **Graceful degradation** throughout the system

---

## Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key (or Google Gemini / OpenRouter)
- PostgreSQL (production) or SQLite (development)
- SendGrid API key (for email delivery)

### Installation

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Configure environment
cp env.example .env
# Edit .env with your API keys

# 3. Run server
uvicorn main:app --reload --port 8000

# 4. Access application
# Landing page: http://localhost:8000
# Dashboard: http://localhost:8000/dashboard.html
# API docs: http://localhost:8000/docs
```

### First Use

1. Register an account at `/auth.html`
2. Set your location in Settings (`/profile.html`)
3. Generate your first digest from the dashboard
4. Configure email notifications (optional)

---

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### User Management
- `GET /api/users/me` - Get profile
- `PUT /api/users/me` - Update profile

### Preferences
- `GET /api/preferences` - Get settings
- `PUT /api/preferences` - Update settings

### Digests
- `POST /api/digests/generate` - Generate digest
- `GET /api/digests` - List history
- `GET /api/digests/{id}` - Get specific digest
- `GET /api/digests/latest` - Get latest

---

## Architecture Highlights

### Multi-Agent Pipeline

```
User Request (location: "Melbourne CBD")
    ↓
Monitor Agent: Search for crime/safety news
    ↓
Relevance Agent: Filter by proximity & severity
    ↓
Summary Agent: Generate concise summaries
    ↓
Digest Agent: Synthesize top 3 incidents
    ↓
Database: Save digest
    ↓
Email: Deliver to user
```

### Database Schema

- **users**: Authentication and profile
- **user_preferences**: Location and notification settings
- **news_digests**: Generated digests with articles
- **news_articles**: Article cache for deduplication

### Security

- JWT authentication with 24-hour expiry
- Bcrypt password hashing
- SQL injection prevention via ORM
- CORS middleware for API security

---

## Documentation

For detailed information, see:

- **User Guide**: `NEWS_AGENT_README.md`
- **Technical Specification**: `NEWS_AGENT_SPEC.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`

---

## Deployment

### Local Development
```bash
uvicorn main:app --reload --port 8000
```

### Production (Render, Railway, etc.)
1. Set environment variables in dashboard
2. Build command: `pip install -r backend/requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Project Status

✅ **Complete and Production-Ready**

- All core features implemented
- Comprehensive documentation
- Error handling and graceful degradation
- Security best practices
- Observability and monitoring

**Next Steps**: Deploy, customize, or extend with additional features!

---

## License

MIT License

## Support

For issues or questions, please open an issue on GitHub.

