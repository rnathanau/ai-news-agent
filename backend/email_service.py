"""Email service for sending news digests to users."""

import os
from typing import Optional, List
from datetime import datetime
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv

load_dotenv()

def _get_sendgrid_api_key():
    """Get SendGrid API key from environment."""
    return os.getenv("SENDGRID_API_KEY")

def _get_from_email():
    """Get FROM_EMAIL from environment."""
    return os.getenv("FROM_EMAIL", "notifications@newsagent.com")

def _is_email_enabled():
    """Check if email is enabled (API key is set)."""
    return bool(_get_sendgrid_api_key())


# HTML Email Template
EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Safety Digest</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            color: #1e40af;
            font-size: 24px;
        }
        .header .date {
            color: #6b7280;
            font-size: 14px;
            margin-top: 5px;
        }
        .location {
            display: inline-block;
            background-color: #dbeafe;
            color: #1e40af;
            padding: 5px 12px;
            border-radius: 4px;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .summary {
            background-color: #f9fafb;
            border-left: 4px solid #2563eb;
            padding: 15px;
            margin-bottom: 30px;
            font-size: 15px;
        }
        .article {
            border-left: 3px solid #e5e7eb;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #fafafa;
        }
        .article h3 {
            margin: 0 0 10px 0;
            color: #1f2937;
            font-size: 18px;
        }
        .article .meta {
            color: #6b7280;
            font-size: 13px;
            margin-bottom: 10px;
        }
        .article .content {
            color: #4b5563;
            font-size: 14px;
            line-height: 1.7;
        }
        .article .full-content {
            color: #374151;
            font-size: 14px;
            margin-top: 10px;
            line-height: 1.8;
        }
        .article a {
            color: #2563eb;
            text-decoration: none;
            font-weight: 500;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
        }
        .footer a {
            color: #2563eb;
            text-decoration: none;
        }
        .button {
            display: inline-block;
            background-color: #2563eb;
            color: #ffffff !important;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 20px;
        }
        .no-incidents {
            text-align: center;
            padding: 40px 20px;
            color: #059669;
        }
        .no-incidents h2 {
            color: #059669;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Daily Safety Digest</h1>
            <div class="date">{{ date }}</div>
        </div>
        
        <div class="location">Location: {{ location }}</div>
        
        {% if has_incidents %}
            <div class="summary">
                <strong>Today's Overview:</strong><br>
                {{ overview }}
            </div>
            
            {% for article in articles %}
            <div class="article">
                <h3>{{ loop.index }}. {{ article.title }}</h3>
                <div class="meta">
                    {% if article.source %}📰 {{ article.source }} • {% endif %}
                    {% if article.published_at %}📅 {{ article.published_at }}{% endif %}
                </div>
                <div class="content">
                    <strong>Summary:</strong> {{ article.summary }}
                </div>
                {% if article.content and article.content|length > 100 %}
                <div class="full-content">
                    {{ article.content[:400] }}{% if article.content|length > 400 %}...{% endif %}
                </div>
                {% endif %}
                {% if article.url and article.url != '#' %}
                <div style="margin-top: 10px;">
                    <a href="{{ article.url }}" style="font-size: 13px;">📖 Read full article on {{ article.source }}</a>
                </div>
                {% endif %}
            </div>
            {% endfor %}
            
            <center>
                <a href="{{ dashboard_url }}" class="button">View Full Digest</a>
            </center>
        {% else %}
            <div class="no-incidents">
                <h2>All Clear!</h2>
                <p>No significant safety incidents to report in your area today.<br>Stay safe and have a great day!</p>
            </div>
        {% endif %}
        
        <div class="footer">
            <p>
                This digest was generated by AI News Agent<br>
                <a href="{{ unsubscribe_url }}">Manage preferences</a> | 
                <a href="{{ dashboard_url }}">View dashboard</a>
            </p>
            <p style="margin-top: 10px;">
                You're receiving this because you subscribed to safety updates for {{ location }}.
            </p>
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
        digest_id: Optional[int] = None
    ) -> bool:
        """Send a digest email to a user.
        
        Args:
            to_email: Recipient email address
            location: Location for the digest
            articles: List of article dicts with title, summary, url, source
            summary: Overall digest summary
            digest_id: Optional digest ID for dashboard link
        
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
                unsubscribe_url=unsubscribe_url
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
            
            # Create email message with personalized subject
            subject = f"Your Daily {location} Safety Update - {datetime.now().strftime('%b %d, %Y')}"
            
            message = Mail(
                from_email=Email(from_email, "HeadsUp Safety Alert"),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", plain_text),
                html_content=Content("text/html", html_content)
            )
            
            # Add categories for tracking and better deliverability
            message.add_category("daily_digest")
            message.add_category("safety_news")
            
            # Note: custom_arg removed as it was causing serialization issues with SendGrid API
            # Tracking can be done via categories and SendGrid dashboard
            
            print("DEBUG: About to send email via SendGrid")
            # Send email
            try:
                response = client.send(message)
                print(f"DEBUG: SendGrid response status: {response.status_code}")
                
                if response.status_code in [200, 201, 202]:
                    print(f"Email sent successfully to {to_email}")
                    return True
                else:
                    print(f"Failed to send email. Status: {response.status_code}")
                    return False
            except Exception as send_error:
                print(f"SendGrid send error: {type(send_error).__name__}: {str(send_error)}")
                import traceback
                traceback.print_exc()
                raise
                
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


def send_digest_email(to_email: str, location: str, articles: List[dict], summary: str, digest_id: Optional[int] = None) -> bool:
    """Convenience function to send digest email.
    
    Args:
        to_email: Recipient email address
        location: Location for the digest
        articles: List of article dicts
        summary: Overall digest summary
        digest_id: Optional digest ID
    
    Returns:
        True if sent successfully
    """
    return email_service.send_digest_email(to_email, location, articles, summary, digest_id)

