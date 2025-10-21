from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import os
import time
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Database and authentication imports
from database import get_db, init_db
import models, schemas, auth

# Minimal observability via Arize/OpenInference (optional)
try:
    from arize.otel import register as arize_register
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from openinference.instrumentation.litellm import LiteLLMInstrumentor
    from openinference.instrumentation import using_prompt_template, using_metadata, using_attributes
    from opentelemetry import trace
    _TRACING = True
except Exception:
    def using_prompt_template(**kwargs):  # type: ignore
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()
    def using_metadata(*args, **kwargs):  # type: ignore
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()
    def using_attributes(*args, **kwargs):  # type: ignore
        from contextlib import contextmanager
        @contextmanager
        def _noop():
            yield
        return _noop()
    _TRACING = False

# LangGraph + LangChain
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict, Annotated
import operator
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
import httpx


class TripRequest(BaseModel):
    destination: str
    duration: str
    budget: Optional[str] = None
    interests: Optional[str] = None
    travel_style: Optional[str] = None
    # Optional fields for enhanced session tracking and observability
    user_input: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    turn_index: Optional[int] = None


class TripResponse(BaseModel):
    result: str
    tool_calls: List[Dict[str, Any]] = []


def _init_llm():
    # Simple, test-friendly LLM init
    class _Fake:
        def __init__(self):
            pass
        def bind_tools(self, tools):
            return self
        def invoke(self, messages):
            class _Msg:
                content = "Test itinerary"
                tool_calls: List[Dict[str, Any]] = []
            return _Msg()

    if os.getenv("TEST_MODE"):
        return _Fake()
    if os.getenv("GOOGLE_API_KEY"):
        # Use Google Gemini
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_MODEL", "gemini-pro"),
                temperature=0.7,
                google_api_key=os.getenv("GOOGLE_API_KEY"),
            )
        except ImportError:
            raise ValueError("Please install langchain-google-genai: pip install langchain-google-genai")
    elif os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.7, max_tokens=1500)
    elif os.getenv("OPENROUTER_API_KEY"):
        # Use OpenRouter via OpenAI-compatible client
        return ChatOpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            temperature=0.7,
        )
    else:
        # Require a key unless running tests
        raise ValueError("Please set GOOGLE_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY in your .env")


llm = _init_llm()


# Feature flag for optional RAG demo (opt-in for learning)
ENABLE_RAG = os.getenv("ENABLE_RAG", "0").lower() not in {"0", "false", "no"}


# RAG helper: Load curated local guides as LangChain documents
def _load_local_documents(path: Path) -> List[Document]:
    """Load local guides JSON and convert to LangChain Documents."""
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text())
    except Exception:
        return []

    docs: List[Document] = []
    for row in raw:
        description = row.get("description")
        city = row.get("city")
        if not description or not city:
            continue
        interests = row.get("interests", []) or []
        metadata = {
            "city": city,
            "interests": interests,
            "source": row.get("source"),
        }
        # Prefix city + interests in content so embeddings capture location context
        interest_text = ", ".join(interests) if interests else "general travel"
        content = f"City: {city}\nInterests: {interest_text}\nGuide: {description}"
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


class LocalGuideRetriever:
    """Retrieves curated local experiences using vector similarity search.
    
    This class demonstrates production RAG patterns for students:
    - Vector embeddings for semantic search
    - Fallback to keyword matching when embeddings unavailable
    - Graceful degradation with feature flags
    """
    
    def __init__(self, data_path: Path):
        """Initialize retriever with local guides data.
        
        Args:
            data_path: Path to local_guides.json file
        """
        self._docs = _load_local_documents(data_path)
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._vectorstore: Optional[InMemoryVectorStore] = None
        
        # Only create embeddings when RAG is enabled and we have an API key
        if ENABLE_RAG and self._docs and not os.getenv("TEST_MODE"):
            try:
                model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
                self._embeddings = OpenAIEmbeddings(model=model)
                store = InMemoryVectorStore(embedding=self._embeddings)
                store.add_documents(self._docs)
                self._vectorstore = store
            except Exception:
                # Gracefully degrade to keyword search if embeddings fail
                self._embeddings = None
                self._vectorstore = None

    @property
    def is_empty(self) -> bool:
        """Check if any documents were loaded."""
        return not self._docs

    def retrieve(self, destination: str, interests: Optional[str], *, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant local guides for a destination.
        
        Args:
            destination: City or destination name
            interests: Comma-separated interests (e.g., "food, art")
            k: Number of results to return
            
        Returns:
            List of dicts with 'content', 'metadata', and 'score' keys
        """
        if not ENABLE_RAG or self.is_empty:
            return []

        # Use vector search if available, otherwise fall back to keywords
        if not self._vectorstore:
            return self._keyword_fallback(destination, interests, k=k)

        query = destination
        if interests:
            query = f"{destination} with interests {interests}"
        
        try:
            # LangChain retriever ensures embeddings + searches are traced
            retriever = self._vectorstore.as_retriever(search_kwargs={"k": max(k, 4)})
            docs = retriever.invoke(query)
        except Exception:
            return self._keyword_fallback(destination, interests, k=k)

        # Format results with metadata and scores
        top_docs = docs[:k]
        results = []
        for doc in top_docs:
            score_val: float = 0.0
            if isinstance(doc.metadata, dict):
                maybe_score = doc.metadata.get("score")
                if isinstance(maybe_score, (int, float)):
                    score_val = float(maybe_score)
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score_val,
            })

        if not results:
            return self._keyword_fallback(destination, interests, k=k)
        return results

    def _keyword_fallback(self, destination: str, interests: Optional[str], *, k: int) -> List[Dict[str, Any]]:
        """Simple keyword-based retrieval when embeddings unavailable.
        
        This demonstrates graceful degradation for students learning about
        fallback strategies in production systems.
        """
        dest_lower = destination.lower()
        interest_terms = [part.strip().lower() for part in (interests or "").split(",") if part.strip()]

        def _score(doc: Document) -> int:
            score = 0
            city_match = doc.metadata.get("city", "").lower()
            # Match city name
            if dest_lower and dest_lower.split(",")[0] in city_match:
                score += 2
            # Match interests
            for term in interest_terms:
                if term and term in " ".join(doc.metadata.get("interests") or []).lower():
                    score += 1
                if term and term in doc.page_content.lower():
                    score += 1
            return score

        scored_docs = [(_score(doc), doc) for doc in self._docs]
        scored_docs.sort(key=lambda item: item[0], reverse=True)
        top_docs = scored_docs[:k]
        
        results = []
        for score, doc in top_docs:
            if score > 0:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                })
        return results


# Initialize retriever at module level (loads data once at startup)
_DATA_DIR = Path(__file__).parent / "data"
GUIDE_RETRIEVER = LocalGuideRetriever(_DATA_DIR / "local_guides.json")


# Search API configuration and helpers
SEARCH_TIMEOUT = 10.0  # seconds


def _compact(text: str, limit: int = 200) -> str:
    """Compact text to a maximum length, truncating at word boundaries."""
    if not text:
        return ""
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[:limit]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated.rstrip(",.;- ")


def _search_api_articles(query: str, max_results: int = 5, days: int = 2) -> List[Dict[str, Any]]:
    """Search for news articles with full metadata including URLs.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        days: Only return articles from the last N days (default: 2)
    
    Returns list of articles with: title, url, content, source, published_at
    """
    query = query.strip()
    if not query:
        return []

    # Try Tavily first (recommended for news search)
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            print(f"[Tavily] Searching for: {query}")
            with httpx.Client(timeout=SEARCH_TIMEOUT) as client:
                resp = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "max_results": max_results,
                        "search_depth": "advanced",  # Use advanced for better recency
                        "include_answer": False,
                        "topic": "news",  # Force news-only results
                        "days": days,  # Only search last N days
                        "exclude_domains": ["wikipedia.org", "wikimedia.org", "britannica.com"],  # No encyclopedias
                    },
                )
                print(f"[Tavily] Response status: {resp.status_code}")
                resp.raise_for_status()
                data = resp.json()
                
                results_count = len(data.get("results", []))
                print(f"[Tavily] Found {results_count} results")
                
                articles = []
                current_time = datetime.now()
                
                for item in data.get("results", []):
                    url = item.get("url", "")
                    
                    # Skip invalid or example URLs
                    if not url or url == "#" or "example.com" in url or "localhost" in url:
                        print(f"[Tavily] Skipping invalid URL: {url}")
                        continue
                    
                    # Parse published date if available
                    published_at = item.get("published_date")
                    if published_at:
                        try:
                            # Try to parse the date
                            if isinstance(published_at, str):
                                from dateutil import parser as date_parser
                                pub_date = date_parser.parse(published_at)
                                # Filter out articles older than specified days
                                age_days = (current_time - pub_date.replace(tzinfo=None)).days
                                if age_days > days:
                                    print(f"[Tavily] Skipping old article (age: {age_days} days): {item.get('title', 'Untitled')}")
                                    continue
                        except Exception as e:
                            print(f"[Tavily] Error parsing date {published_at}: {e}")
                    
                    articles.append({
                        "title": item.get("title", "Untitled"),
                        "url": url,
                        "content": item.get("content", ""),
                        "source": url.split("/")[2] if url and len(url.split("/")) > 2 else "Unknown",
                        "published_at": published_at
                    })
                
                if articles:
                    print(f"[Tavily] Returning {len(articles)} recent articles")
                    print(f"[Tavily] First article: {articles[0].get('title', 'No title')}")
                return articles
        except Exception as e:
            print(f"[Tavily] API error: {e}")
            print(f"[Tavily] Error type: {type(e).__name__}")
            pass  # Fail gracefully, try next option
    else:
        print("[Tavily] No API key found in environment")
    
    return []


def _search_api(query: str) -> Optional[str]:
    """Search the web using Tavily or SerpAPI if configured, return None otherwise.
    
    This demonstrates graceful degradation: tools work with or without API keys.
    Students can enable real search by adding TAVILY_API_KEY or SERPAPI_API_KEY.
    """
    query = query.strip()
    if not query:
        return None

    # Try Tavily first (recommended for AI apps)
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            with httpx.Client(timeout=SEARCH_TIMEOUT) as client:
                resp = client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": query,
                        "max_results": 3,
                        "search_depth": "basic",
                        "include_answer": True,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("answer") or ""
                snippets = [
                    item.get("content") or item.get("snippet") or ""
                    for item in data.get("results", [])
                ]
                combined = " ".join([answer] + snippets).strip()
                if combined:
                    return _compact(combined)
        except Exception:
            pass  # Fail gracefully, try next option

    # Try SerpAPI as fallback
    serp_key = os.getenv("SERPAPI_API_KEY")
    if serp_key:
        try:
            with httpx.Client(timeout=SEARCH_TIMEOUT) as client:
                resp = client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": serp_key,
                        "engine": "google",
                        "num": 5,
                        "q": query,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                organic = data.get("organic_results", [])
                snippets = [item.get("snippet", "") for item in organic]
                combined = " ".join(snippets).strip()
                if combined:
                    return _compact(combined)
        except Exception:
            pass  # Fail gracefully

    return None  # No search APIs configured


def _llm_fallback(instruction: str, context: Optional[str] = None) -> str:
    """Use the LLM to generate a response when search APIs aren't available.
    
    This ensures tools always return useful information, even without API keys.
    """
    prompt = "Respond with 200 characters or less.\n" + instruction.strip()
    if context:
        prompt += "\nContext:\n" + context.strip()
    response = llm.invoke([
        SystemMessage(content="You are a concise travel assistant."),
        HumanMessage(content=prompt),
    ])
    return _compact(response.content)


def _with_prefix(prefix: str, summary: str) -> str:
    """Add a prefix to a summary for clarity."""
    text = f"{prefix}: {summary}" if prefix else summary
    return _compact(text)


# Tools with real API calls + LLM fallback (graceful degradation pattern)
@tool
def essential_info(destination: str) -> str:
    """Return essential destination info like weather, sights, and etiquette."""
    query = f"{destination} travel essentials weather best time top attractions etiquette language currency safety"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} essentials", summary)
    
    # LLM fallback when no search API is configured
    instruction = f"Summarize the climate, best visit time, standout sights, customs, language, currency, and safety tips for {destination}."
    return _llm_fallback(instruction)


@tool
def budget_basics(destination: str, duration: str) -> str:
    """Return high-level budget categories for a given destination and duration."""
    query = f"{destination} travel budget average daily costs {duration}"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} budget {duration}", summary)
    
    instruction = f"Outline lodging, meals, transport, activities, and extra costs for a {duration} trip to {destination}."
    return _llm_fallback(instruction)


@tool
def local_flavor(destination: str, interests: Optional[str] = None) -> str:
    """Suggest authentic local experiences matching optional interests."""
    focus = interests or "local culture"
    query = f"{destination} authentic local experiences {focus}"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} {focus}", summary)
    
    instruction = f"Recommend authentic local experiences in {destination} that highlight {focus}."
    return _llm_fallback(instruction)


@tool
def day_plan(destination: str, day: int) -> str:
    """Return a simple day plan outline for a specific day number."""
    query = f"{destination} day {day} itinerary highlights"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"Day {day} in {destination}", summary)
    
    instruction = f"Outline key activities for day {day} in {destination}, covering morning, afternoon, and evening."
    return _llm_fallback(instruction)


# Additional simple tools per agent (to mirror original multi-tool behavior)
@tool
def weather_brief(destination: str) -> str:
    """Return a brief weather summary for planning purposes."""
    query = f"{destination} weather forecast travel season temperatures rainfall"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} weather", summary)
    
    instruction = f"Give a weather brief for {destination} noting season, temperatures, rainfall, humidity, and packing guidance."
    return _llm_fallback(instruction)


@tool
def visa_brief(destination: str) -> str:
    """Return a brief visa guidance for travel planning."""
    query = f"{destination} tourist visa requirements entry rules"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} visa", summary)
    
    instruction = f"Provide a visa guidance summary for visiting {destination}, including advice to confirm with the relevant embassy."
    return _llm_fallback(instruction)


@tool
def attraction_prices(destination: str, attractions: Optional[List[str]] = None) -> str:
    """Return pricing information for attractions."""
    items = attractions or ["popular attractions"]
    focus = ", ".join(items)
    query = f"{destination} attraction ticket prices {focus}"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} attraction prices", summary)
    
    instruction = f"Share typical ticket prices and savings tips for attractions such as {focus} in {destination}."
    return _llm_fallback(instruction)


@tool
def local_customs(destination: str) -> str:
    """Return cultural etiquette and customs information."""
    query = f"{destination} cultural etiquette travel customs"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} customs", summary)
    
    instruction = f"Summarize key etiquette and cultural customs travelers should know before visiting {destination}."
    return _llm_fallback(instruction)


@tool
def hidden_gems(destination: str) -> str:
    """Return lesser-known attractions and experiences."""
    query = f"{destination} hidden gems local secrets lesser known spots"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} hidden gems", summary)
    
    instruction = f"List lesser-known attractions or experiences that feel like hidden gems in {destination}."
    return _llm_fallback(instruction)


@tool
def travel_time(from_location: str, to_location: str, mode: str = "public") -> str:
    """Return travel time estimates between locations."""
    query = f"travel time {from_location} to {to_location} by {mode}"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{from_location}→{to_location} {mode}", summary)
    
    instruction = f"Estimate travel time from {from_location} to {to_location} by {mode} transport."
    return _llm_fallback(instruction)


@tool
def packing_list(destination: str, duration: str, activities: Optional[List[str]] = None) -> str:
    """Return packing recommendations for the trip."""
    acts = ", ".join(activities or ["sightseeing"])
    query = f"what to pack for {destination} {duration} {acts}"
    summary = _search_api(query)
    if summary:
        return _with_prefix(f"{destination} packing", summary)
    
    instruction = f"Suggest packing essentials for a {duration} trip to {destination} focused on {acts}."
    return _llm_fallback(instruction)


# ============================================================================
# NEWS AGENT TOOLS - For crime/safety monitoring
# ============================================================================

@tool
def search_local_news(location: str, keywords: str = "crime theft burglary", days_back: int = 1) -> str:
    """Search for recent crime and safety news in a specific location.
    
    Args:
        location: City, neighborhood, or address to search
        keywords: Crime/safety related keywords to search for
        days_back: Number of days to search back (default 1 for daily digest)
    
    Returns:
        Summary of recent news articles with titles, sources, and brief descriptions
    """
    query = f"{location} {keywords} news last {days_back} days"
    summary = _search_api(query)
    
    if summary:
        return _with_prefix(f"{location} crime news", summary)
    
    # LLM fallback
    instruction = f"Summarize recent crime and safety incidents in {location} related to: {keywords}. Include typical local issues if real data unavailable."
    return _llm_fallback(instruction, context=f"Location: {location}")


@tool
def extract_location_details(article_text: str) -> str:
    """Extract specific location details (addresses, neighborhoods) from news article text.
    
    Args:
        article_text: News article content to parse
    
    Returns:
        Structured location information extracted from the article
    """
    # Use LLM to extract location details
    instruction = f"Extract and list all specific locations mentioned (addresses, intersections, neighborhoods) from this text: {article_text[:500]}"
    return _llm_fallback(instruction)


@tool
def calculate_proximity(incident_location: str, user_location: str) -> str:
    """Calculate approximate distance between incident and user location.
    
    Args:
        incident_location: Location where incident occurred
        user_location: User's location for comparison
    
    Returns:
        Distance estimate and proximity rating (near/medium/far)
    """
    # Simple search-based distance estimation
    query = f"distance from {user_location} to {incident_location}"
    summary = _search_api(query)
    
    if summary:
        return summary
    
    # LLM fallback
    instruction = f"Estimate the approximate distance between {user_location} and {incident_location}. Indicate if they are in the same neighborhood, nearby areas, or distant."
    return _llm_fallback(instruction)


@tool
def severity_score(article_text: str, incident_type: str) -> str:
    """Analyze crime severity and assign a relevance score.
    
    Args:
        article_text: News article content
        incident_type: Type of crime (theft, burglary, assault, etc.)
    
    Returns:
        Severity assessment (low/medium/high) and reasoning
    """
    # Use LLM to assess severity
    instruction = f"Analyze this {incident_type} incident and rate its severity (low/medium/high) for neighborhood safety awareness: {article_text[:300]}"
    return _llm_fallback(instruction)


@tool
def classify_incident_type(article_text: str) -> str:
    """Classify the type of crime or safety incident from article text.
    
    Args:
        article_text: News article content
    
    Returns:
        Primary incident type (theft, burglary, assault, vandalism, etc.)
    """
    instruction = f"Classify the main type of crime or safety incident in this article (theft, burglary, home invasion, assault, vandalism, traffic, fire, etc.): {article_text[:400]}"
    return _llm_fallback(instruction)


@tool
def summarize_article(article_text: str, title: str) -> str:
    """Generate a concise 2-3 sentence summary of a news article.
    
    Args:
        article_text: Full or partial article content
        title: Article title
    
    Returns:
        Concise summary highlighting key facts (what, where, when)
    """
    instruction = f"Summarize this news article in 2-3 sentences, focusing on what happened, where, and when. Title: {title}. Content: {article_text[:500]}"
    return _llm_fallback(instruction)


# ============================================================================
# STATE DEFINITIONS
# ============================================================================

class TripState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    trip_request: Dict[str, Any]
    research: Optional[str]
    budget: Optional[str]
    local: Optional[str]
    final: Optional[str]
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]


class NewsDigestState(TypedDict):
    """State for news digest generation workflow."""
    messages: Annotated[List[BaseMessage], operator.add]
    digest_request: Dict[str, Any]  # Contains location, user_id, date, etc.
    raw_articles: Optional[List[Dict[str, Any]]]  # From monitor_agent
    ranked_articles: Optional[List[Dict[str, Any]]]  # From relevance_agent
    article_summaries: Optional[List[Dict[str, Any]]]  # From summary_agent
    final_digest: Optional[str]  # From digest_agent
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]


# ============================================================================
# TRIP PLANNER AGENTS (Legacy - keeping for reference)
# ============================================================================

def research_agent(state: TripState) -> TripState:
    req = state["trip_request"]
    destination = req["destination"]
    prompt_t = (
        "You are a research assistant.\n"
        "Gather essential information about {destination}.\n"
        "Use tools to get weather, visa, and essential info, then summarize."
    )
    vars_ = {"destination": destination}
    
    messages = [SystemMessage(content=prompt_t.format(**vars_))]
    tools = [essential_info, weather_brief, visa_brief]
    agent = llm.bind_tools(tools)
    
    calls: List[Dict[str, Any]] = []
    tool_results = []
    
    # Agent metadata and prompt template instrumentation
    with using_attributes(tags=["research", "info_gathering"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "research")
                current_span.set_attribute("metadata.agent_node", "research_agent")
        
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = agent.invoke(messages)
    
    # Collect tool calls and execute them
    if getattr(res, "tool_calls", None):
        for c in res.tool_calls:
            calls.append({"agent": "research", "tool": c["name"], "args": c.get("args", {})})
        
        tool_node = ToolNode(tools)
        tr = tool_node.invoke({"messages": [res]})
        tool_results = tr["messages"]
        
        # Add tool results to conversation and ask LLM to synthesize
        messages.append(res)
        messages.extend(tool_results)
        
        synthesis_prompt = "Based on the above information, provide a comprehensive summary for the traveler."
        messages.append(SystemMessage(content=synthesis_prompt))
        
        # Instrument synthesis LLM call with its own prompt template
        synthesis_vars = {"destination": destination, "context": "tool_results"}
        with using_prompt_template(template=synthesis_prompt, variables=synthesis_vars, version="v1-synthesis"):
            final_res = llm.invoke(messages)
        out = final_res.content
    else:
        out = res.content

    return {"messages": [SystemMessage(content=out)], "research": out, "tool_calls": calls}


def budget_agent(state: TripState) -> TripState:
    req = state["trip_request"]
    destination, duration = req["destination"], req["duration"]
    budget = req.get("budget", "moderate")
    prompt_t = (
        "You are a budget analyst.\n"
        "Analyze costs for {destination} over {duration} with budget: {budget}.\n"
        "Use tools to get pricing information, then provide a detailed breakdown."
    )
    vars_ = {"destination": destination, "duration": duration, "budget": budget}
    
    messages = [SystemMessage(content=prompt_t.format(**vars_))]
    tools = [budget_basics, attraction_prices]
    agent = llm.bind_tools(tools)
    
    calls: List[Dict[str, Any]] = []
    
    # Agent metadata and prompt template instrumentation
    with using_attributes(tags=["budget", "cost_analysis"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "budget")
                current_span.set_attribute("metadata.agent_node", "budget_agent")
        
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = agent.invoke(messages)
    
    if getattr(res, "tool_calls", None):
        for c in res.tool_calls:
            calls.append({"agent": "budget", "tool": c["name"], "args": c.get("args", {})})
        
        tool_node = ToolNode(tools)
        tr = tool_node.invoke({"messages": [res]})
        
        # Add tool results and ask for synthesis
        messages.append(res)
        messages.extend(tr["messages"])
        
        synthesis_prompt = f"Create a detailed budget breakdown for {duration} in {destination} with a {budget} budget."
        messages.append(SystemMessage(content=synthesis_prompt))
        
        # Instrument synthesis LLM call
        synthesis_vars = {"duration": duration, "destination": destination, "budget": budget}
        with using_prompt_template(template=synthesis_prompt, variables=synthesis_vars, version="v1-synthesis"):
            final_res = llm.invoke(messages)
        out = final_res.content
    else:
        out = res.content

    return {"messages": [SystemMessage(content=out)], "budget": out, "tool_calls": calls}


def local_agent(state: TripState) -> TripState:
    req = state["trip_request"]
    destination = req["destination"]
    interests = req.get("interests", "local culture")
    travel_style = req.get("travel_style", "standard")
    
    # RAG: Retrieve curated local guides if enabled
    context_lines = []
    if ENABLE_RAG:
        retrieved = GUIDE_RETRIEVER.retrieve(destination, interests, k=3)
        if retrieved:
            context_lines.append("=== Curated Local Guides (from database) ===")
            for idx, item in enumerate(retrieved, 1):
                content = item["content"]
                source = item["metadata"].get("source", "Unknown")
                context_lines.append(f"{idx}. {content}")
                context_lines.append(f"   Source: {source}")
            context_lines.append("=== End of Curated Guides ===\n")
    
    context_text = "\n".join(context_lines) if context_lines else ""
    
    prompt_t = (
        "You are a local guide.\n"
        "Find authentic experiences in {destination} for someone interested in: {interests}.\n"
        "Travel style: {travel_style}. Use tools to gather local insights.\n"
    )
    
    # Add retrieved context to prompt if available
    if context_text:
        prompt_t += "\nRelevant curated experiences from our database:\n{context}\n"
    
    vars_ = {
        "destination": destination,
        "interests": interests,
        "travel_style": travel_style,
        "context": context_text if context_text else "No curated context available.",
    }
    
    messages = [SystemMessage(content=prompt_t.format(**vars_))]
    tools = [local_flavor, local_customs, hidden_gems]
    agent = llm.bind_tools(tools)
    
    calls: List[Dict[str, Any]] = []
    
    # Agent metadata and prompt template instrumentation
    with using_attributes(tags=["local", "local_experiences"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "local")
                current_span.set_attribute("metadata.agent_node", "local_agent")
                if ENABLE_RAG and context_text:
                    current_span.set_attribute("metadata.rag_enabled", "true")
        
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = agent.invoke(messages)
    
    if getattr(res, "tool_calls", None):
        for c in res.tool_calls:
            calls.append({"agent": "local", "tool": c["name"], "args": c.get("args", {})})
        
        tool_node = ToolNode(tools)
        tr = tool_node.invoke({"messages": [res]})
        
        # Add tool results and ask for synthesis
        messages.append(res)
        messages.extend(tr["messages"])
        
        synthesis_prompt = f"Create a curated list of authentic experiences for someone interested in {interests} with a {travel_style} approach."
        messages.append(SystemMessage(content=synthesis_prompt))
        
        # Instrument synthesis LLM call
        synthesis_vars = {"interests": interests, "travel_style": travel_style, "destination": destination}
        with using_prompt_template(template=synthesis_prompt, variables=synthesis_vars, version="v1-synthesis"):
            final_res = llm.invoke(messages)
        out = final_res.content
    else:
        out = res.content

    return {"messages": [SystemMessage(content=out)], "local": out, "tool_calls": calls}


def itinerary_agent(state: TripState) -> TripState:
    req = state["trip_request"]
    destination = req["destination"]
    duration = req["duration"]
    travel_style = req.get("travel_style", "standard")
    user_input = (req.get("user_input") or "").strip()
    
    prompt_parts = [
        "Create a {duration} itinerary for {destination} ({travel_style}).",
        "",
        "Inputs:",
        "Research: {research}",
        "Budget: {budget}",
        "Local: {local}",
    ]
    if user_input:
        prompt_parts.append("User input: {user_input}")
    
    prompt_t = "\n".join(prompt_parts)
    vars_ = {
        "duration": duration,
        "destination": destination,
        "travel_style": travel_style,
        "research": (state.get("research") or "")[:400],
        "budget": (state.get("budget") or "")[:400],
        "local": (state.get("local") or "")[:400],
        "user_input": user_input,
    }
    
    # Add span attributes for better observability in Arize
    # NOTE: using_attributes must be OUTER context for proper propagation
    with using_attributes(tags=["itinerary", "final_agent"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.itinerary", "true")
                current_span.set_attribute("metadata.agent_type", "itinerary")
                current_span.set_attribute("metadata.agent_node", "itinerary_agent")
                if user_input:
                    current_span.set_attribute("metadata.user_input", user_input)
        
        # Prompt template wrapper for Arize Playground integration
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = llm.invoke([SystemMessage(content=prompt_t.format(**vars_))])
    
    return {"messages": [SystemMessage(content=res.content)], "final": res.content}


# ============================================================================
# NEWS AGENT SYSTEM - For crime/safety monitoring
# ============================================================================

def monitor_agent(state: NewsDigestState) -> NewsDigestState:
    """Monitor agent: Searches for recent crime/safety news in user's location."""
    req = state["digest_request"]
    location = req["location"]
    keywords = req.get("keywords", "crime theft burglary home invasion safety")
    days_back = req.get("days_back", 1)
    
    prompt_t = (
        "You are a news monitoring agent.\n"
        "Search for recent crime and safety incidents in {location}.\n"
        "Focus on: {keywords}.\n"
        "Use the search_local_news tool to find articles from the last {days_back} days."
    )
    vars_ = {"location": location, "keywords": keywords, "days_back": days_back}
    
    messages = [SystemMessage(content=prompt_t.format(**vars_))]
    tools = [search_local_news, classify_incident_type]
    agent = llm.bind_tools(tools)
    
    calls: List[Dict[str, Any]] = []
    articles = []
    
    with using_attributes(tags=["monitor", "news_search"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "monitor")
                current_span.set_attribute("metadata.location", location)
        
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = agent.invoke(messages)
    
    # Try to get real articles from Tavily API first
    # Craft highly specific query for local breaking news only
    from datetime import datetime, timedelta
    date_range = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    
    # Use news-specific search with site restrictions to avoid Wikipedia/stats
    # Focus on local news outlets, police reports, and breaking news
    query = f'"{location}" ({keywords}) site:.com.au OR site:.gov.au OR site:police OR site:news after:{date_range} -site:wikipedia.org -site:abc.net.au/news/archive'
    
    print(f"[Monitor Agent] Searching for breaking news with query: {query}")
    real_articles = _search_api_articles(query, max_results=15, days=days_back)
    
    if real_articles:
        # Use real articles from Tavily
        articles = [{
            **article,
            "found_via": "tavily_api"
        } for article in real_articles]
        calls.append({"agent": "monitor", "tool": "tavily_search", "args": {"query": query}})
        print(f"[Monitor Agent] Found {len(articles)} real articles from Tavily")
    elif getattr(res, "tool_calls", None):
        # Fallback to LLM tool calls if no Tavily results
        print("[Monitor Agent] No Tavily results, using LLM tool calls")
        for c in res.tool_calls:
            calls.append({"agent": "monitor", "tool": c["name"], "args": c.get("args", {})})
        
        tool_node = ToolNode(tools)
        tr = tool_node.invoke({"messages": [res]})
        
        # IMPORTANT: Only use LLM fallback if explicitly needed
        # We should NOT show fake URLs to users
        articles = []
        print("[Monitor Agent] WARNING: Using LLM fallback - no real articles found")
        print("[Monitor Agent] Consider adding TAVILY_API_KEY to environment for real news")
    else:
        articles = []
        print("[Monitor Agent] No articles found")
    
    return {
        "messages": [SystemMessage(content=f"Found {len(articles)} potential articles")],
        "raw_articles": articles,
        "tool_calls": calls
    }


def relevance_agent(state: NewsDigestState) -> NewsDigestState:
    """Relevance agent: Filters and ranks articles by proximity and severity."""
    req = state["digest_request"]
    location = req["location"]
    raw_articles = state.get("raw_articles", [])
    severity_threshold = req.get("severity_threshold", "all")
    radius_km = req.get("radius_km", 5)
    days_back = req.get("days_back", 1)
    
    if not raw_articles:
        return {
            "messages": [SystemMessage(content="No articles to rank")],
            "ranked_articles": [],
            "tool_calls": []
        }
    
    # Filter out articles with invalid URLs first
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days_back + 1)  # Allow 1 extra day buffer
    
    valid_articles = []
    for article in raw_articles:
        url = article.get("url", "")
        
        # Skip invalid URLs
        if not url or url == "#" or "example.com" in url or "localhost" in url:
            print(f"[Relevance Agent] Filtering out article with invalid URL: {article.get('title', 'Untitled')}")
            continue
        
        # Check recency if published_at is available
        published_at = article.get("published_at")
        if published_at:
            try:
                if isinstance(published_at, str):
                    from dateutil import parser as date_parser
                    pub_date = date_parser.parse(published_at)
                    if pub_date.replace(tzinfo=None) < cutoff_date:
                        print(f"[Relevance Agent] Filtering out old article: {article.get('title', 'Untitled')} (published: {published_at})")
                        continue
            except Exception as e:
                print(f"[Relevance Agent] Error parsing date for {article.get('title', 'Untitled')}: {e}")
        
        valid_articles.append(article)
    
    print(f"[Relevance Agent] Filtered to {len(valid_articles)} valid recent articles from {len(raw_articles)} total")
    
    if not valid_articles:
        return {
            "messages": [SystemMessage(content="No valid recent articles found")],
            "ranked_articles": [],
            "tool_calls": []
        }
    
    prompt_t = (
        "You are a relevance ranking agent.\n"
        "Analyze {num_articles} articles and rank them by:\n"
        "1. Proximity to {location} (within {radius_km}km)\n"
        "2. Severity ({severity_threshold} threshold)\n"
        "3. Recency (last {days_back} days)\n"
        "Return the top 3-5 most relevant articles."
    )
    vars_ = {
        "num_articles": len(valid_articles),
        "location": location,
        "radius_km": radius_km,
        "severity_threshold": severity_threshold,
        "days_back": days_back
    }
    
    messages = [SystemMessage(content=prompt_t.format(**vars_))]
    # Add article context
    for idx, article in enumerate(valid_articles[:10], 1):  # Limit to first 10
        pub_info = f" (Published: {article.get('published_at', 'unknown')})" if article.get('published_at') else ""
        messages.append(HumanMessage(content=f"Article {idx}: {article.get('title', 'Untitled')}{pub_info} - {article.get('content', '')[:200]}"))
    
    tools = [calculate_proximity, severity_score, extract_location_details]
    agent = llm.bind_tools(tools)
    
    calls: List[Dict[str, Any]] = []
    
    with using_attributes(tags=["relevance", "ranking"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "relevance")
                current_span.set_attribute("metadata.articles_count", len(valid_articles))
        
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = agent.invoke(messages)
    
    if getattr(res, "tool_calls", None):
        for c in res.tool_calls:
            calls.append({"agent": "relevance", "tool": c["name"], "args": c.get("args", {})})
        
        tool_node = ToolNode(tools)
        tr = tool_node.invoke({"messages": [res]})
    
    # Take top 5 articles (more than 3 to give digest agent more options)
    ranked = valid_articles[:5]
    print(f"[Relevance Agent] Ranked top {len(ranked)} articles")
    
    return {
        "messages": [SystemMessage(content=f"Ranked {len(ranked)} relevant articles")],
        "ranked_articles": ranked,
        "tool_calls": calls
    }


def summary_agent(state: NewsDigestState) -> NewsDigestState:
    """Summary agent: Generates concise summaries for each article."""
    ranked_articles = state.get("ranked_articles", [])
    
    if not ranked_articles:
        return {
            "messages": [SystemMessage(content="No articles to summarize")],
            "article_summaries": [],
            "tool_calls": []
        }
    
    prompt_t = "You are a news summarization agent. Create concise 2-3 sentence summaries for each article."
    messages = [SystemMessage(content=prompt_t)]
    
    tools = [summarize_article]
    agent = llm.bind_tools(tools)
    
    calls: List[Dict[str, Any]] = []
    summaries = []
    
    with using_attributes(tags=["summary", "summarization"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "summary")
        
        # Summarize each article
        for article in ranked_articles:
            title = article.get("title", "Untitled")
            content = article.get("content", "")
            
            result = summarize_article.invoke({"article_text": content, "title": title})
            
            summaries.append({
                **article,
                "summary": result
            })
            calls.append({"agent": "summary", "tool": "summarize_article", "args": {"title": title}})
    
    return {
        "messages": [SystemMessage(content=f"Summarized {len(summaries)} articles")],
        "article_summaries": summaries,
        "tool_calls": calls
    }


def digest_agent(state: NewsDigestState) -> NewsDigestState:
    """Digest agent: Synthesizes top 3 articles into a cohesive safety briefing."""
    req = state["digest_request"]
    location = req["location"]
    article_summaries = state.get("article_summaries", [])
    
    if not article_summaries:
        final_digest = f"# Daily Safety Digest for {location}\n\nNo significant incidents to report today. Stay safe!"
        return {
            "messages": [SystemMessage(content=final_digest)],
            "final_digest": final_digest,
            "tool_calls": []
        }
    
    prompt_t = (
        "Create a safety briefing for {location}.\n"
        "Synthesize these {num_articles} incident summaries into a clear, informative digest.\n"
        "Format:\n"
        "- Brief overview (do NOT include time of day like 'morning' or 'evening')\n"
        "- Top 3 incidents with key details\n"
        "- Safety recommendations\n\n"
        "Articles:\n{articles_text}"
    )
    
    articles_text = "\n\n".join([
        f"{idx}. {art.get('title', 'Untitled')}\n   {art.get('summary', 'No summary')}"
        for idx, art in enumerate(article_summaries, 1)
    ])
    
    vars_ = {
        "location": location,
        "num_articles": len(article_summaries),
        "articles_text": articles_text
    }
    
    with using_attributes(tags=["digest", "synthesis"]):
        if _TRACING:
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("metadata.agent_type", "digest")
                current_span.set_attribute("metadata.location", location)
        
        with using_prompt_template(template=prompt_t, variables=vars_, version="v1"):
            res = llm.invoke([SystemMessage(content=prompt_t.format(**vars_))])
    
    return {
        "messages": [SystemMessage(content=res.content)],
        "final_digest": res.content,
        "tool_calls": []
    }


def build_news_digest_graph():
    """Build LangGraph workflow for news digest generation."""
    g = StateGraph(NewsDigestState)
    g.add_node("monitor_node", monitor_agent)
    g.add_node("relevance_node", relevance_agent)
    g.add_node("summary_node", summary_agent)
    g.add_node("digest_node", digest_agent)
    
    # Sequential flow: monitor -> relevance -> summary -> digest
    g.add_edge(START, "monitor_node")
    g.add_edge("monitor_node", "relevance_node")
    g.add_edge("relevance_node", "summary_node")
    g.add_edge("summary_node", "digest_node")
    g.add_edge("digest_node", END)
    
    return g.compile()


def build_graph():
    g = StateGraph(TripState)
    g.add_node("research_node", research_agent)
    g.add_node("budget_node", budget_agent)
    g.add_node("local_node", local_agent)
    g.add_node("itinerary_node", itinerary_agent)

    # Run research, budget, and local agents in parallel
    g.add_edge(START, "research_node")
    g.add_edge(START, "budget_node")
    g.add_edge(START, "local_node")
    
    # All three agents feed into the itinerary agent
    g.add_edge("research_node", "itinerary_node")
    g.add_edge("budget_node", "itinerary_node")
    g.add_edge("local_node", "itinerary_node")
    
    g.add_edge("itinerary_node", END)

    # Compile without checkpointer to avoid state persistence issues
    return g.compile()


app = FastAPI(title="AI News Agent", description="Personalized news digest for local crime and safety")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event to initialize database and scheduler
@app.on_event("startup")
def startup_event():
    """Initialize database and scheduler on application startup."""
    init_db()
    print("Database initialized successfully")
    
    # Start scheduler for automated digest generation
    try:
        from scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"Failed to start scheduler: {e}")


@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on application shutdown."""
    try:
        from scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


@app.get("/")
def serve_frontend():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "frontend", "index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "frontend/index.html not found"}


@app.get("/auth.html")
def serve_auth():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "frontend", "auth.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "frontend/auth.html not found"}


@app.get("/dashboard.html")
def serve_dashboard():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "frontend", "dashboard.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "frontend/dashboard.html not found"}


@app.get("/profile.html")
def serve_profile():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "frontend", "profile.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "frontend/profile.html not found"}


@app.get("/test-email.html")
def serve_test_email():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "..", "frontend", "test-email.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "frontend/test-email.html not found"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "ai-news-agent"}


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=schemas.Token, tags=["Authentication"])
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if user already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default preferences
    preferences = models.UserPreferences(user_id=db_user.id)
    db.add(preferences)
    db.commit()
    
    # Generate access token
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=schemas.Token, tags=["Authentication"])
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    """Login with email and password."""
    db_user = auth.authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=schemas.UserResponse, tags=["Authentication"])
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    """Get current user information."""
    return current_user


# ============================================================================
# User Profile & Preferences Endpoints
# ============================================================================

@app.get("/api/users/me", response_model=schemas.UserResponse, tags=["Users"])
def read_user_me(current_user: models.User = Depends(auth.get_current_user)):
    """Get current user profile."""
    return current_user


@app.put("/api/users/me", response_model=schemas.UserResponse, tags=["Users"])
def update_user_me(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    if user_update.email:
        # Check if email is already taken by another user
        existing = db.query(models.User).filter(
            models.User.email == user_update.email,
            models.User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email
    
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.password:
        current_user.hashed_password = auth.get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user


@app.get("/api/preferences", response_model=schemas.UserPreferencesResponse, tags=["Preferences"])
def get_preferences(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences."""
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences if they don't exist
        prefs = models.UserPreferences(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return prefs


@app.put("/api/preferences", response_model=schemas.UserPreferencesResponse, tags=["Preferences"])
def update_preferences(
    prefs_update: schemas.UserPreferencesUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences."""
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = models.UserPreferences(user_id=current_user.id)
        db.add(prefs)
    
    # Update fields
    update_data = prefs_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    return prefs


# ============================================================================
# News Digest Endpoints
# ============================================================================

@app.post("/api/digests/generate", response_model=schemas.NewsDigestResponse, tags=["Digests"])
def generate_digest(
    request: schemas.NewsDigestRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a news digest for the user's location or a specified location."""
    # Get user preferences
    prefs = db.query(models.UserPreferences).filter(
        models.UserPreferences.user_id == current_user.id
    ).first()
    
    # Use request location or fall back to user's primary location
    location = request.location or (prefs.primary_location if prefs else None)
    
    if not location:
        raise HTTPException(
            status_code=400,
            detail="No location specified. Please provide a location or set your primary location in preferences."
        )
    
    # Build digest request
    digest_request = {
        "location": location,
        "user_id": current_user.id,
        "date": request.date or datetime.now(),
        "keywords": "crime theft burglary home invasion safety",
        "days_back": 1,
        "severity_threshold": prefs.severity_threshold if prefs else "all",
        "radius_km": prefs.radius_km if prefs else 5
    }
    
    # Build and invoke news digest graph
    graph = build_news_digest_graph()
    state = {
        "messages": [],
        "digest_request": digest_request,
        "tool_calls": []
    }
    
    with using_attributes(user_id=str(current_user.id)):
        result = graph.invoke(state)
    
    # Extract articles and digest
    articles = result.get("article_summaries", [])
    final_digest = result.get("final_digest", "No digest generated")
    
    # Save digest to database
    digest = models.NewsDigest(
        user_id=current_user.id,
        location=location,
        digest_date=digest_request["date"],
        articles=articles,
        summary_text=final_digest,
        email_sent=False
    )
    db.add(digest)
    db.commit()
    db.refresh(digest)
    
    return digest


@app.get("/api/digests", response_model=schemas.NewsDigestListResponse, tags=["Digests"])
def list_digests(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 30
):
    """Get list of user's historical digests (last 30 days by default)."""
    digests = db.query(models.NewsDigest).filter(
        models.NewsDigest.user_id == current_user.id
    ).order_by(
        models.NewsDigest.digest_date.desc()
    ).offset(skip).limit(limit).all()
    
    total = db.query(models.NewsDigest).filter(
        models.NewsDigest.user_id == current_user.id
    ).count()
    
    return {
        "digests": digests,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit
    }


@app.get("/api/digests/{digest_id}", response_model=schemas.NewsDigestResponse, tags=["Digests"])
def get_digest(
    digest_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific digest by ID."""
    digest = db.query(models.NewsDigest).filter(
        models.NewsDigest.id == digest_id,
        models.NewsDigest.user_id == current_user.id
    ).first()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    return digest


@app.get("/api/digests/latest", response_model=schemas.NewsDigestResponse, tags=["Digests"])
def get_latest_digest(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get the most recent digest for the current user."""
    digest = db.query(models.NewsDigest).filter(
        models.NewsDigest.user_id == current_user.id
    ).order_by(
        models.NewsDigest.digest_date.desc()
    ).first()
    
    if not digest:
        raise HTTPException(status_code=404, detail="No digests found. Generate your first digest!")
    
    return digest


# Initialize Arize AX tracing once at startup
if _TRACING:
    try:
        space_id = os.getenv("ARIZE_SPACE_ID")
        api_key = os.getenv("ARIZE_API_KEY")
        project_name = os.getenv("ARIZE_PROJECT_NAME", "headsup-news-agent")
        
        if space_id and api_key:
            # Set environment variables for arize-otel to read automatically
            os.environ["ARIZE_SPACE_ID"] = space_id
            os.environ["ARIZE_API_KEY"] = api_key
            os.environ["ARIZE_PROJECT_NAME"] = project_name
            
            # Register with Arize AX - it will read from environment variables
            tp = arize_register()
            
            # Instrument LangChain for automatic tracing of agents, chains, and tools
            LangChainInstrumentor().instrument(
                tracer_provider=tp,
                include_chains=True,
                include_agents=True,
                include_tools=True
            )
            # Instrument LiteLLM for LLM call tracing
            LiteLLMInstrumentor().instrument(tracer_provider=tp, skip_dep_check=True)
            print("✅ Arize AX tracing initialized for HeadsUp News Agent")
            print(f"   Project: {project_name} | Space: {space_id[:20]}...")
    except Exception as e:
        print(f"⚠️ Arize tracing not available: {e}")


# ============================================================================
# Test & Manual Trigger Endpoints
# ============================================================================

@app.post("/api/test-email", tags=["Testing"])
def test_email(current_user: models.User = Depends(auth.get_current_user)):
    """Send a test email to verify SendGrid configuration."""
    from email_service import email_service
    
    # Debug: Check if API key is loaded
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL")
    print(f"DEBUG: SENDGRID_API_KEY present: {bool(api_key)}")
    print(f"DEBUG: FROM_EMAIL: {from_email}")
    print(f"DEBUG: email_service.enabled: {email_service.enabled}")
    
    if not api_key:
        return {
            "status": "error",
            "message": "SENDGRID_API_KEY environment variable not found"
        }
    
    success = email_service.send_test_email(current_user.email)
    
    if success:
        return {
            "status": "success",
            "message": f"Test email sent to {current_user.email}. Check your inbox (and spam folder)!"
        }
    else:
        return {
            "status": "error",
            "message": "Failed to send test email. Check that SENDGRID_API_KEY is configured in backend/.env"
        }


@app.post("/api/digests/generate-now", response_model=schemas.NewsDigestResponse, tags=["Digests"])
def generate_digest_now(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    send_email: bool = True
):
    """Manually trigger digest generation and optionally send email immediately."""
    from scheduler import generate_digest_for_user
    
    # Generate digest
    success = generate_digest_for_user(current_user.id, db)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate digest. Check logs for details."
        )
    
    # Get the most recent digest
    digest = db.query(models.NewsDigest).filter(
        models.NewsDigest.user_id == current_user.id
    ).order_by(
        models.NewsDigest.digest_date.desc()
    ).first()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest generated but not found in database")
    
    return digest


@app.post("/plan-trip", response_model=TripResponse)
def plan_trip(req: TripRequest):
    graph = build_graph()
    
    # Only include necessary fields in initial state
    # Agent outputs (research, budget, local, final) will be added during execution
    state = {
        "messages": [],
        "trip_request": req.model_dump(),
        "tool_calls": [],
    }
    
    # Add session and user tracking attributes to the trace
    session_id = req.session_id
    user_id = req.user_id
    turn_idx = req.turn_index
    
    # Build attributes for session and user tracking
    attrs_kwargs = {}
    if session_id:
        attrs_kwargs["session_id"] = session_id
    if user_id:
        attrs_kwargs["user_id"] = user_id
    
    # Add turn_index as a custom span attribute if provided
    if turn_idx is not None and _TRACING:
        with using_attributes(**attrs_kwargs):
            current_span = trace.get_current_span()
            if current_span:
                current_span.set_attribute("turn_index", turn_idx)
            out = graph.invoke(state)
    else:
        with using_attributes(**attrs_kwargs):
            out = graph.invoke(state)
    
    return TripResponse(result=out.get("final", ""), tool_calls=out.get("tool_calls", []))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
