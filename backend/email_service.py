"""Email service for sending news digests to users."""

import os
from typing import Optional, List
from datetime import datetime
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Category
from dotenv import load_dotenv

load_dotenv()

def _get_sendgrid_api_key():
    """Get SendGrid API key from environment."""
    return os.getenv("SENDGRID_API_KEY")

def _get_from_email():
    """Get FROM_EMAIL from environment."""
    email = os.getenv("FROM_EMAIL", "notifications@newsagent.com")
    # Strip any whitespace or newlines
    return email.strip() if email else "notifications@newsagent.com"

def _is_email_enabled():
    """Check if email is enabled (API key is set)."""
    return bool(_get_sendgrid_api_key())

def _get_time_based_greeting(location: str, timezone_str: str = "UTC") -> dict:
    """Get time-based greeting and subject line based on user's timezone.
    
    Args:
        location: Location name for personalization
        timezone_str: User's timezone (e.g., "Australia/Melbourne", "America/New_York")
    
    Returns:
        dict with 'subject', 'greeting', and 'emoji' keys
    """
    import pytz
    
    # Get current time in user's timezone
    try:
        user_tz = pytz.timezone(timezone_str)
        local_time = datetime.now(user_tz)
        hour = local_time.hour
    except:
        # Fallback to UTC if timezone is invalid
        hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return {
            "subject": f"🌅 Good Morning! Your {location} Safety Digest",
            "greeting": "Good Morning",
            "emoji": "🌅",
            "time_of_day": "morning"
        }
    elif 12 <= hour < 17:
        return {
            "subject": f"☀️ Afternoon Check-In: {location} Safety Update",
            "greeting": "Good Afternoon",
            "emoji": "☀️",
            "time_of_day": "afternoon"
        }
    else:
        return {
            "subject": f"🌆 Evening Briefing: Your {location} Safety Digest",
            "greeting": "Good Evening",
            "emoji": "🌆",
            "time_of_day": "evening"
        }


# HTML Email Template - Modern & Attractive Design
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HeadsUp Safety Digest</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.7;
            color: #1f2937;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px 15px;
        }
        .container {
            max-width: 650px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header .subtitle {
            font-size: 16px;
            opacity: 0.95;
            font-weight: 500;
        }
        .content {
            padding: 35px 30px;
        }
        .location-badge {
            display: inline-flex;
            align-items: center;
            background: #eff6ff;
            color: #1e40af;
            padding: 10px 18px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 25px;
            border: 2px solid #dbeafe;
        }
        .overview-card {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            border-left: 5px solid #3b82f6;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            font-size: 16px;
            line-height: 1.8;
        }
        .overview-card strong {
            color: #1e40af;
            font-size: 17px;
        }
        .incident-card {
            background: #fafafa;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .incident-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .incident-number {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            text-align: center;
            line-height: 32px;
            font-weight: 700;
            margin-right: 10px;
            font-size: 16px;
        }
        .incident-title {
            color: #111827;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 12px;
            line-height: 1.4;
        }
        .incident-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 16px;
            font-size: 13px;
            color: #6b7280;
        }
        .meta-item {
            display: inline-flex;
            align-items: center;
            background: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 500;
        }
        .incident-summary {
            color: #374151;
            font-size: 15px;
            line-height: 1.8;
            margin-bottom: 12px;
            padding: 16px;
            background: white;
            border-radius: 8px;
            border-left: 3px solid #e5e7eb;
        }
        .incident-details {
            color: #4b5563;
            font-size: 14px;
            line-height: 1.8;
            padding: 14px;
            background: #f9fafb;
            border-radius: 8px;
            margin-top: 12px;
        }
        .read-more {
            display: inline-flex;
            align-items: center;
            margin-top: 14px;
            color: #3b82f6;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: color 0.2s;
        }
        .read-more:hover {
            color: #1d4ed8;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            padding: 16px 36px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: 700;
            font-size: 16px;
            margin-top: 30px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        .no-incidents {
            text-align: center;
            padding: 60px 30px;
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            border-radius: 12px;
            margin: 20px 0;
        }
        .no-incidents-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        .no-incidents h2 {
            color: #047857;
            font-size: 28px;
            margin-bottom: 12px;
        }
        .no-incidents p {
            color: #065f46;
            font-size: 16px;
            line-height: 1.6;
        }
        .footer {
            background: #f9fafb;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }
        .footer-brand {
            font-weight: 700;
            font-size: 14px;
            color: #6366f1;
            margin-bottom: 15px;
        }
        .footer-links {
            margin: 15px 0;
        }
        .footer-links a {
            color: #6366f1;
            text-decoration: none;
            font-weight: 600;
            margin: 0 12px;
            font-size: 13px;
        }
        .footer-note {
            color: #9ca3af;
            font-size: 12px;
            margin-top: 15px;
            line-height: 1.6;
        }
        @media (max-width: 600px) {
            .header h1 { font-size: 26px; }
            .incident-title { font-size: 18px; }
            .content { padding: 25px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{{ greeting_emoji }} {{ greeting }}!</h1>
            <div class="subtitle">{{ date }}</div>
        </div>
        
        <!-- Main Content -->
        <div class="content">
            <div class="location-badge">📍 {{ location }}</div>
            
            {% if has_incidents %}
                <!-- Overview -->
                <div class="overview-card">
                    <strong>Today's Overview</strong><br>
                    {{ overview }}
                </div>
                
                <!-- Incidents -->
                {% for article in articles %}
                <div class="incident-card">
                    <div class="incident-title">
                        <span class="incident-number">{{ loop.index }}</span>
                        {{ article.title }}
                    </div>
                    
                    <div class="incident-meta">
                        {% if article.published_at %}
                        <span class="meta-item">📅 {{ article.published_at }}</span>
                        {% endif %}
                        {% if article.source %}
                        <span class="meta-item">📰 {{ article.source }}</span>
                        {% endif %}
                        {% if article.location %}
                        <span class="meta-item">📍 {{ article.location }}</span>
                        {% endif %}
                    </div>
                    
                    <div class="incident-summary">
                        {{ article.summary }}
                    </div>
                    
                    {% if article.content and article.content|length > 100 %}
                    <div class="incident-details">
                        {{ article.content[:450] }}{% if article.content|length > 450 %}...{% endif %}
                    </div>
                    {% endif %}
                    
                    {% if article.url and article.url != '#' %}
                    <a href="{{ article.url }}" class="read-more">
                        📖 Read full article →
                    </a>
                    {% endif %}
                </div>
                {% endfor %}
                
                <!-- CTA -->
                <center>
                    <a href="{{ dashboard_url }}" class="cta-button">
                        View Full Dashboard →
                    </a>
                </center>
                
            {% else %}
                <!-- No Incidents -->
                <div class="no-incidents">
                    <div class="no-incidents-icon">✨🛡️✨</div>
                    <h2>All Clear!</h2>
                    <p>
                        No significant safety incidents to report in your area today.<br>
                        Stay safe and have a wonderful day!
                    </p>
                </div>
            {% endif %}
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <div class="footer-brand">⚡ HeadsUp Safety Alert</div>
            <div class="footer-links">
                <a href="{{ dashboard_url }}">Dashboard</a>
                <a href="{{ unsubscribe_url }}">Manage Preferences</a>
            </div>
            <div class="footer-note">
                You're receiving this because you subscribed to safety updates for {{ location }}.<br>
                Powered by HeadsUp AI
            </div>
        </div>
    </div>
</body>
</html>
"""


class EmailService:
    """Service for sending email notifications to users."""
    
    def __init__(self):
        """Initialize email service."""
        # Don't cache the client - create it on demand
        pass
    
    def _get_client(self):
        """Get SendGrid client (creates on demand)."""
        api_key = _get_sendgrid_api_key()
        if not api_key:
            return None
        return SendGridAPIClient(api_key)
    
    @property
    def enabled(self):
        """Check if email is enabled."""
        return _is_email_enabled()
    
    def send_digest_email(
        self,
        to_email: str,
        location: str,
        articles: List[dict],
        summary: str,
        digest_id: Optional[int] = None,
        timezone: str = "UTC"
    ) -> bool:
        """Send a digest email to a user.
        
        Args:
            to_email: Recipient email address
            location: Location for the digest
            articles: List of article dicts with title, summary, url, source
            summary: Overall digest summary
            digest_id: Optional digest ID for dashboard link
            timezone: User's timezone for time-based greeting
        
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"Email sending disabled. Would have sent to {to_email}")
            return False
        
        try:
            # Get client dynamically
            client = self._get_client()
            if not client:
                print("SendGrid client not available")
                return False
            
            from_email = _get_from_email()
            print(f"DEBUG: Preparing email from {from_email} to {to_email}")
            print(f"DEBUG: Articles type: {type(articles)}, count: {len(articles)}")
            if articles:
                print(f"DEBUG: First article type: {type(articles[0])}")
                print(f"DEBUG: First article: {articles[0]}")
            
            # Prepare template data with actual Render domain
            app_domain = os.getenv("APP_DOMAIN", "https://ai-news-agent-foz7.onrender.com")
            dashboard_url = f"{app_domain}/dashboard.html"
            unsubscribe_url = f"{app_domain}/profile.html"
            
            has_incidents = len(articles) > 0
            
            # Extract brief overview from summary (first sentence)
            overview = summary.split('.')[0] + '.' if summary else "No incidents to report."
            
            # Format date
            date_str = datetime.now().strftime("%A, %B %d, %Y")
            
            # Get time-based greeting using user's timezone
            time_greeting = _get_time_based_greeting(location, timezone)
            
            print("DEBUG: About to render HTML template")
            # Render HTML template
            template = Template(EMAIL_TEMPLATE)
            html_content = template.render(
                date=date_str,
                location=location,
                has_incidents=has_incidents,
                overview=overview,
                articles=articles[:5],  # Top 5 articles for comprehensive coverage
                dashboard_url=dashboard_url,
                unsubscribe_url=unsubscribe_url,
                greeting=time_greeting["greeting"],
                greeting_emoji=time_greeting["emoji"]
            )
            print("DEBUG: HTML template rendered successfully")
            
            # Create plain text version (improves deliverability)
            plain_text = f"""
Daily Safety Digest - {date_str}
Location: {location}

{overview}

"""
            if has_incidents:
                for idx, article in enumerate(articles[:5], 1):
                    # Handle both dict and object access
                    title = article.get('title', 'Untitled') if isinstance(article, dict) else getattr(article, 'title', 'Untitled')
                    summary = article.get('summary', '') if isinstance(article, dict) else getattr(article, 'summary', '')
                    url = article.get('url') if isinstance(article, dict) else getattr(article, 'url', None)
                    
                    plain_text += f"{idx}. {title}\n"
                    plain_text += f"   {summary}\n"
                    if url and url != '#':
                        plain_text += f"   Read more: {url}\n"
                    plain_text += "\n"
            else:
                plain_text += "All Clear! No significant safety incidents to report today.\n\n"
            
            plain_text += f"\nView dashboard: {dashboard_url}\n"
            plain_text += f"Manage preferences: {unsubscribe_url}\n"
            
            print("DEBUG: Plain text version created successfully")
            
            # Create email message with time-based personalized subject
            subject = time_greeting["subject"]
            
            message = Mail(
                from_email=Email(from_email, "HeadsUp Safety Alert"),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", plain_text),
                html_content=Content("text/html", html_content)
            )
            
            # Add categories for tracking and better deliverability
            message.add_category(Category("daily_digest"))
            message.add_category(Category("safety_news"))
            
            # Note: custom_arg removed as it was causing serialization issues with SendGrid API
            # Tracking can be done via categories and SendGrid dashboard
            
            print("DEBUG: About to send email via SendGrid")
            # Debug: Print the message payload
            try:
                message_dict = message.get()
                print(f"DEBUG: Message payload keys: {list(message_dict.keys())}")
                print(f"DEBUG: From: {message_dict.get('from')}")
                print(f"DEBUG: Personalizations: {message_dict.get('personalizations')}")
                print(f"DEBUG: Categories: {message_dict.get('categories')}")
            except Exception as debug_err:
                print(f"DEBUG: Could not serialize message: {debug_err}")
            
            # Send email
            try:
                response = client.send(message)
                print(f"DEBUG: SendGrid response status: {response.status_code}")
                
                if response.status_code in [200, 201, 202]:
                    print(f"Email sent successfully to {to_email}")
                    return True
                else:
                    print(f"Failed to send email. Status: {response.status_code}")
                    print(f"Response body: {response.body}")
                    print(f"Response headers: {response.headers}")
                    return False
            except Exception as send_error:
                print(f"SendGrid send error: {type(send_error).__name__}: {str(send_error)}")
                # Try to get more details from the HTTP error
                if hasattr(send_error, 'to_dict'):
                    print(f"Error dict: {send_error.to_dict}")
                # For python_http_client exceptions, check the response
                import sys
                exc_info = sys.exc_info()
                if exc_info[2] is not None:
                    # Get the last frame which should have the response
                    import traceback as tb
                    for frame_summary in tb.extract_tb(exc_info[2]):
                        print(f"Frame: {frame_summary.filename}:{frame_summary.lineno} in {frame_summary.name}")
                
                # The error message might be in the exception args
                if hasattr(send_error, 'args') and len(send_error.args) > 0:
                    print(f"Error args: {send_error.args}")
                
                import traceback
                traceback.print_exc()
                
                # Don't raise, return False so we can see the error message
                return False
                
        except Exception as e:
            print(f"Error sending email to {to_email}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration.
        
        Args:
            to_email: Recipient email address
        
        Returns:
            True if email sent successfully, False otherwise
        """
        test_articles = [
            {
                "title": "Test Incident 1",
                "summary": "This is a test summary for a safety incident in your area.",
                "source": "Test Source",
                "url": "#",
                "published_at": "Just now"
            }
        ]
        
        return self.send_digest_email(
            to_email=to_email,
            location="Test Location",
            articles=test_articles,
            summary="This is a test digest email from AI News Agent.",
            digest_id=None
        )


# Global email service instance
email_service = EmailService()


def send_digest_email(to_email: str, location: str, articles: List[dict], summary: str, digest_id: Optional[int] = None, timezone: str = "UTC") -> bool:
    """Convenience function to send digest email.
    
    Args:
        to_email: Recipient email address
        location: Location for the digest
        articles: List of article dicts
        summary: Overall digest summary
        digest_id: Optional digest ID
        timezone: User's timezone for time-based greeting
    
    Returns:
        True if sent successfully
    """
    return email_service.send_digest_email(to_email, location, articles, summary, digest_id, timezone)

