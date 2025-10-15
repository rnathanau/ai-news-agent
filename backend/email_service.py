"""Email service for sending news digests to users."""

import os
from typing import Optional, List
from datetime import datetime
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "notifications@newsagent.com")
ENABLE_EMAIL = bool(SENDGRID_API_KEY)  # Only enable if API key is set


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
            <h1>🛡️ Daily Safety Digest</h1>
            <div class="date">{{ date }}</div>
        </div>
        
        <div class="location">📍 {{ location }}</div>
        
        {% if has_incidents %}
            <div class="summary">
                <strong>Today's Overview:</strong><br>
                {{ overview }}
            </div>
            
            {% for article in articles %}
            <div class="article">
                <h3>{{ loop.index }}. {{ article.title }}</h3>
                <div class="meta">
                    {% if article.source %}{{ article.source }} • {% endif %}
                    {% if article.published_at %}{{ article.published_at }}{% endif %}
                </div>
                <div class="content">
                    {{ article.summary }}
                    {% if article.url and article.url != '#' %}
                    <br><a href="{{ article.url }}">Read full article →</a>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            
            <center>
                <a href="{{ dashboard_url }}" class="button">View Full Digest</a>
            </center>
        {% else %}
            <div class="no-incidents">
                <h2>✅ All Clear!</h2>
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
        self.enabled = ENABLE_EMAIL
        if self.enabled:
            self.client = SendGridAPIClient(SENDGRID_API_KEY)
        else:
            self.client = None
    
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
            # Prepare template data
            dashboard_url = f"https://newsagent.com/dashboard.html"  # Update with actual domain
            unsubscribe_url = f"https://newsagent.com/profile.html"  # Update with actual domain
            
            has_incidents = len(articles) > 0
            
            # Extract brief overview from summary (first sentence)
            overview = summary.split('.')[0] + '.' if summary else "No incidents to report."
            
            # Format date
            date_str = datetime.now().strftime("%A, %B %d, %Y")
            
            # Render HTML template
            template = Template(EMAIL_TEMPLATE)
            html_content = template.render(
                date=date_str,
                location=location,
                has_incidents=has_incidents,
                overview=overview,
                articles=articles[:3],  # Top 3 only
                dashboard_url=dashboard_url,
                unsubscribe_url=unsubscribe_url
            )
            
            # Create email message
            subject = f"🛡️ Safety Digest for {location} - {datetime.now().strftime('%b %d')}"
            
            message = Mail(
                from_email=Email(FROM_EMAIL, "AI News Agent"),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                print(f"❌ Failed to send email. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending email to {to_email}: {str(e)}")
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

