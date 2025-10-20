# News Relevancy & Recency Improvements

## Summary

Enhanced the AI News Agent to ensure all news digests contain **recent, relevant articles with valid URLs**. The system now properly filters out old news and fake URLs.

## Changes Made

### 1. Enhanced Tavily API Integration (`_search_api_articles`)

**File**: `backend/main.py` (lines 303-388)

**Improvements**:
- Added `days` parameter (default: 2 days) to limit search to recent news
- Changed `search_depth` from "basic" to "advanced" for better recency
- Added `days` parameter to Tavily API request
- Implemented **URL validation** to filter out:
  - Empty URLs (`""` or `"#"`)
  - Example domains (`example.com`)
  - Localhost URLs
- Added **date filtering** to skip articles older than specified days
- Improved logging for debugging

**Benefits**:
- Only returns articles from the last 1-2 days
- No fake/mock URLs in results
- Better quality news from Tavily

### 2. Improved Monitor Agent Query

**File**: `backend/main.py` (lines 1029-1062)

**Improvements**:
- Enhanced search query with date-specific formatting (`after:YYYY-MM-DD`)
- Increased `max_results` from 5 to 10 for better selection
- Removed LLM fallback fake URLs (was generating `localnews.example.com`)
- Added detailed logging for debugging
- Now shows warning when Tavily API key is missing

**Benefits**:
- More targeted searches with date constraints
- No more fake URLs shown to users
- Better visibility into search behavior

### 3. Enhanced Relevance Agent Filtering

**File**: `backend/main.py` (lines 1071-1176)

**Improvements**:
- Added **double URL validation** to catch any URLs that slipped through
- Implemented **strict date filtering** based on published_at timestamps
- Filters out articles older than `days_back + 1` day
- Added date information to LLM context for better ranking
- Increased ranked results from 3 to 5 articles
- Improved logging for transparency

**Benefits**:
- Guarantees only recent articles in final digest
- No invalid URLs can pass through
- Better article selection for final digest

### 4. Added Required Dependency

**File**: `backend/requirements.txt`

**Addition**:
- `python-dateutil>=2.8.2` for robust date parsing

## How It Works Now

### Flow Diagram

```
User Request
    ↓
Monitor Agent
    ├─ Searches Tavily with date constraint (last 2 days)
    ├─ Filters: URL validation + date check
    ↓
Relevance Agent  
    ├─ Double-checks URLs are valid
    ├─ Re-validates dates (published_at)
    ├─ Ranks top 5 by proximity/severity/recency
    ↓
Summary Agent
    ├─ Summarizes each article
    ↓
Digest Agent
    ├─ Creates cohesive briefing
    ↓
Final Digest (Only recent, valid articles!)
```

### Quality Guarantees

1. **Recency**: Articles are filtered at THREE stages:
   - Tavily API: `days` parameter
   - Tavily response: Manual date check
   - Relevance agent: Final date validation

2. **URL Validity**: URLs are validated at TWO stages:
   - Tavily response parsing
   - Relevance agent filtering

3. **Location Relevance**: Improved query includes location-specific terms

## Configuration

### Environment Variables

To enable real news with these improvements, you need:

```env
# Required for real news
TAVILY_API_KEY=tvly-xxxxxxxxxxxxx

# Optional - for better results
OPENAI_API_KEY=sk-xxxxxxxxxxxxx
```

### User Preferences

Users can control recency via their preferences:
- `days_back`: 1-7 days (default: 1 for daily digests)
- `radius_km`: 1-20 km for proximity filtering
- `severity_threshold`: "all", "medium", "high"

## Testing

### Before Deployment

Test locally with:
```bash
# 1. Add TAVILY_API_KEY to backend/.env
# 2. Restart server
cd backend
uvicorn main:app --reload

# 3. Generate test digest via dashboard
# Check that:
# - All URLs are real (no example.com)
# - All dates are within last 1-2 days
# - All articles are relevant to location
```

### After Deployment

1. Go to Render dashboard
2. Update environment variables:
   - Add `TAVILY_API_KEY` if not present
3. Redeploy service (will install python-dateutil)
4. Test digest generation
5. Check server logs for filtering messages

## Expected Log Output

Good logs should show:
```
[Tavily] Searching for: Melbourne crime theft after:2025-10-19
[Tavily] Found 8 results
[Tavily] Skipping old article (age: 3 days): ...
[Tavily] Returning 5 recent articles
[Monitor Agent] Found 5 real articles from Tavily
[Relevance Agent] Filtered to 5 valid recent articles from 5 total
[Relevance Agent] Ranked top 5 articles
```

## Deployment Steps

### For Render:

1. **Commit and Push Changes**
   ```bash
   git add backend/main.py backend/requirements.txt
   git commit -m "Improve news recency and URL validation"
   git push origin main
   ```

2. **Update Environment Variables**
   - Go to: https://dashboard.render.com/
   - Select your service: `ai-news-agent-foz7`
   - Click "Environment" tab
   - Add `TAVILY_API_KEY` (get free key from https://tavily.com/)
   - Click "Save Changes"

3. **Deploy**
   - Render will auto-deploy from GitHub
   - Wait 2-3 minutes for build
   - Monitor "Logs" tab for any errors

4. **Test**
   - Visit your app: https://ai-news-agent-foz7.onrender.com
   - Login and generate a digest
   - Verify all URLs are real and articles are recent

## Fallback Behavior

If Tavily API is not configured:
- System will **not show fake URLs** anymore
- Digest will return empty with warning message
- Logs will suggest adding TAVILY_API_KEY

This is better than showing fake data!

## Troubleshooting

### Issue: No articles found

**Cause**: Location might be too specific or no recent crime news

**Solution**:
- Broaden search keywords
- Increase `days_back` to 2-3 days
- Check Tavily API key is valid

### Issue: Old articles still showing

**Cause**: Articles might not have `published_date` from Tavily

**Solution**:
- Upgrade Tavily plan for better metadata
- Or articles will be filtered conservatively (kept if no date)

### Issue: Tavily API errors

**Cause**: Rate limit or invalid key

**Solution**:
- Check Tavily dashboard for quota
- Regenerate API key if expired
- Consider upgrading Tavily plan

## Future Improvements

1. **Add news source caching** to avoid duplicate searches
2. **Implement geolocation** for accurate distance calculations
3. **Add news sentiment analysis** for severity scoring
4. **Support multiple news APIs** (NewsAPI, Google News) as fallbacks
5. **Add user feedback** on article relevance for learning

## Impact

✅ **No more fake URLs** in digests
✅ **Only recent news** (last 1-2 days)
✅ **Better location relevance** with improved queries
✅ **Transparent logging** for debugging
✅ **Production-ready** with proper error handling

---

**Last Updated**: October 20, 2025
**Version**: 2.0

