"""Diagnostic script to check email digest configuration."""

import os
from dotenv import load_dotenv
from database import SessionLocal
import models

load_dotenv()

def diagnose_email_setup():
    """Check all configuration needed for email digests."""
    
    print("\n" + "="*60)
    print("EMAIL DIGEST DIAGNOSTIC REPORT")
    print("="*60 + "\n")
    
    issues = []
    warnings = []
    
    # 1. Check SendGrid API Key
    print("1. Checking SendGrid Configuration...")
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "notifications@newsagent.com")
    
    if not sendgrid_key or sendgrid_key == "your_sendgrid_api_key_here":
        issues.append("[X] SENDGRID_API_KEY is not configured in backend/.env")
        print("   [X] SendGrid API key is missing or invalid")
    else:
        print(f"   [OK] SendGrid API key is set (length: {len(sendgrid_key)})")
    
    print(f"   FROM_EMAIL: {from_email}")
    
    # 2. Check Scheduler Configuration
    print("\n2. Checking Scheduler Configuration...")
    enable_scheduler = os.getenv("ENABLE_SCHEDULER", "1").lower()
    digest_time = os.getenv("DIGEST_GENERATION_TIME", "00:00")
    
    if enable_scheduler in {"0", "false", "no"}:
        issues.append("[X] ENABLE_SCHEDULER is disabled in backend/.env")
        print(f"   [X] Scheduler is DISABLED (ENABLE_SCHEDULER={enable_scheduler})")
    else:
        print(f"   [OK] Scheduler is enabled")
        print(f"   Digest generation time: {digest_time} UTC")
    
    # 3. Check LLM Configuration
    print("\n3. Checking LLM Configuration...")
    has_llm = False
    if os.getenv("OPENAI_API_KEY"):
        print("   [OK] OpenAI API key is configured")
        has_llm = True
    elif os.getenv("GOOGLE_API_KEY"):
        print("   [OK] Google API key is configured")
        has_llm = True
    elif os.getenv("OPENROUTER_API_KEY"):
        print("   [OK] OpenRouter API key is configured")
        has_llm = True
    else:
        issues.append("[X] No LLM API key configured (OPENAI/GOOGLE/OPENROUTER)")
        print("   [X] No LLM API key found")
    
    # 4. Check Tavily API (for news search)
    print("\n4. Checking News Search API...")
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key or tavily_key == "your_tavily_api_key_here":
        warnings.append("[!] TAVILY_API_KEY not set - will use LLM fallback for news search")
        print("   [!] Tavily API key not set (will use LLM fallback)")
    else:
        print(f"   [OK] Tavily API key is configured")
    
    # 5. Check Database and User Settings
    print("\n5. Checking Database and User Configuration...")
    db = SessionLocal()
    try:
        users = db.query(models.User).filter(models.User.is_active == True).all()
        
        if not users:
            issues.append("[X] No active users found in database")
            print("   [X] No active users in database")
        else:
            print(f"   [OK] Found {len(users)} active user(s)")
            
            for user in users:
                print(f"\n   User: {user.email}")
                
                # Check preferences
                prefs = db.query(models.UserPreferences).filter(
                    models.UserPreferences.user_id == user.id
                ).first()
                
                if not prefs:
                    issues.append(f"[X] User {user.email} has no preferences")
                    print(f"      [X] No preferences found")
                    continue
                
                # Check email notifications
                if not prefs.email_notifications:
                    issues.append(f"[X] User {user.email} has email_notifications disabled")
                    print(f"      [X] Email notifications: DISABLED")
                else:
                    print(f"      [OK] Email notifications: ENABLED")
                
                # Check location
                if not prefs.primary_location:
                    issues.append(f"[X] User {user.email} has no primary_location set")
                    print(f"      [X] Primary location: NOT SET")
                else:
                    print(f"      [OK] Primary location: {prefs.primary_location}")
                
                # Show notification time and timezone
                print(f"      Notification time: {prefs.notification_time} ({prefs.timezone})")
                
                # Check digest history
                digest_count = db.query(models.NewsDigest).filter(
                    models.NewsDigest.user_id == user.id
                ).count()
                print(f"      Digest history: {digest_count} digest(s)")
                
                # Check if any digests were sent via email
                email_sent_count = db.query(models.NewsDigest).filter(
                    models.NewsDigest.user_id == user.id,
                    models.NewsDigest.email_sent == True
                ).count()
                print(f"      Emails sent: {email_sent_count}")
                
    except Exception as e:
        issues.append(f"[X] Database error: {str(e)}")
        print(f"   [X] Database error: {str(e)}")
    finally:
        db.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    if issues:
        print("\n[!] CRITICAL ISSUES (must fix):")
        for issue in issues:
            print(f"   {issue}")
    
    if warnings:
        print("\n[!] WARNINGS (optional but recommended):")
        for warning in warnings:
            print(f"   {warning}")
    
    if not issues:
        print("\n[SUCCESS] All critical checks passed!")
        print("\nIf you still don't receive emails:")
        print("   1. Check your spam/junk folder")
        print("   2. Verify SendGrid sender authentication")
        print("   3. Check backend logs for email sending errors")
        print("   4. Wait for next scheduled digest time")
    else:
        print("\n[ACTION REQUIRED] TO FIX:")
        print("   1. Copy backend/env.example to backend/.env")
        print("   2. Fill in required API keys (SENDGRID_API_KEY, OPENAI_API_KEY or GOOGLE_API_KEY)")
        print("   3. Set your primary_location in the app profile/preferences")
        print("   4. Enable email_notifications in preferences")
        print("   5. Restart the backend server")
    
    print("\n")

if __name__ == "__main__":
    diagnose_email_setup()

