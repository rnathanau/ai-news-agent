"""Scheduler for automated daily digest generation."""

import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from email_service import send_digest_email
# Import build_news_digest_graph later to avoid circular import
from dotenv import load_dotenv

load_dotenv()

# Scheduler configuration
ENABLE_SCHEDULER = os.getenv("ENABLE_SCHEDULER", "1").lower() not in {"0", "false", "no"}
DIGEST_GENERATION_TIME = os.getenv("DIGEST_GENERATION_TIME", "00:00")  # UTC time


scheduler = BackgroundScheduler(timezone=pytz.UTC)


def generate_digest_for_user(user_id: int, db: Session) -> bool:
    """Generate and optionally email a digest for a single user.
    
    Args:
        user_id: User ID to generate digest for
        db: Database session
    
    Returns:
        True if digest generated successfully
    """
    try:
        # Get user and preferences
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or not user.is_active:
            print(f"WARNING: User {user_id} not found or inactive")
            return False
        
        prefs = db.query(models.UserPreferences).filter(
            models.UserPreferences.user_id == user_id
        ).first()
        
        if not prefs or not prefs.primary_location:
            print(f"WARNING: User {user_id} has no location configured")
            return False
        
        # Build digest request
        digest_request = {
            "location": prefs.primary_location,
            "user_id": user_id,
            "date": datetime.now(),
            "keywords": "crime theft burglary home invasion safety",
            "days_back": 1,
            "severity_threshold": prefs.severity_threshold or "all",
            "radius_km": prefs.radius_km or 5
        }
        
        # Generate digest using news agents
        # Import here to avoid circular import at module level
        from main import build_news_digest_graph
        graph = build_news_digest_graph()
        state = {
            "messages": [],
            "digest_request": digest_request,
            "tool_calls": []
        }
        
        result = graph.invoke(state)
        
        # Extract results
        articles = result.get("article_summaries", [])
        final_digest = result.get("final_digest", "No digest generated")
        
        # Save digest to database
        digest = models.NewsDigest(
            user_id=user_id,
            location=prefs.primary_location,
            digest_date=datetime.now(),
            articles=articles,
            summary_text=final_digest,
            email_sent=False
        )
        db.add(digest)
        db.commit()
        db.refresh(digest)
        
        # Send email if enabled
        if prefs.email_notifications:
            email_sent = send_digest_email(
                to_email=user.email,
                location=prefs.primary_location,
                articles=articles,
                summary=final_digest,
                digest_id=digest.id
            )
            
            if email_sent:
                digest.email_sent = True
                digest.email_sent_at = datetime.now()
                db.commit()
        
        print(f"Digest generated for user {user_id} ({user.email}) - Location: {prefs.primary_location}")
        return True
        
    except Exception as e:
        print(f"Error generating digest for user {user_id}: {str(e)}")
        db.rollback()
        return False


def generate_all_digests_job():
    """Job to generate digests for all active users with email notifications enabled.
    
    This job runs daily at the configured time and generates digests for users
    grouped by timezone to deliver at their local preferred time.
    """
    print(f"\n{'='*60}")
    print(f"Starting daily digest generation job at {datetime.now(pytz.UTC)}")
    print(f"{'='*60}\n")
    
    db = SessionLocal()
    try:
        # Get all active users with preferences and email notifications enabled
        users = db.query(models.User).join(
            models.UserPreferences,
            models.User.id == models.UserPreferences.user_id
        ).filter(
            models.User.is_active == True,
            models.UserPreferences.email_notifications == True,
            models.UserPreferences.primary_location.isnot(None)
        ).all()
        
        if not users:
            print("INFO: No users with active subscriptions found")
            return
        
        print(f"INFO: Found {len(users)} users with active subscriptions\n")
        
        success_count = 0
        failed_count = 0
        
        # Generate digest for each user
        for user in users:
            prefs = user.preferences
            
            # Check if it's the right time for this user's timezone
            user_tz = pytz.timezone(prefs.timezone or "UTC")
            user_now = datetime.now(user_tz)
            
            # Parse notification time (HH:MM format)
            try:
                hour, minute = map(int, prefs.notification_time.split(":"))
            except:
                hour, minute = 7, 0  # Default to 7:00 AM
            
            # Check if current time matches user's preferred notification time (within 1 hour window)
            time_diff = abs((user_now.hour * 60 + user_now.minute) - (hour * 60 + minute))
            
            if time_diff <= 60:  # Within 1 hour window
                if generate_digest_for_user(user.id, db):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                print(f"INFO: Skipping user {user.id} - not their notification time yet")
        
        print(f"\n{'='*60}")
        print(f"Daily digest job completed")
        print(f"   Successfully generated: {success_count}")
        print(f"   Failed: {failed_count}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"ERROR: Error in daily digest job: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler for automated digest generation."""
    if not ENABLE_SCHEDULER:
        print("INFO: Scheduler disabled via ENABLE_SCHEDULER environment variable")
        return
    
    # Parse digest generation time
    try:
        hour, minute = map(int, DIGEST_GENERATION_TIME.split(":"))
    except:
        hour, minute = 0, 0  # Default to midnight UTC
    
    # Schedule daily digest generation
    # Run every hour to catch users in different timezones
    scheduler.add_job(
        generate_all_digests_job,
        trigger=CronTrigger(hour='*', minute=0, timezone=pytz.UTC),  # Every hour
        id='generate_all_digests',
        name='Generate daily digests for all users',
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started - Daily digest job will run every hour (UTC)")
    print(f"   Configured base time: {DIGEST_GENERATION_TIME} UTC")


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("Scheduler stopped")


def generate_digest_now(user_id: int) -> bool:
    """Manually trigger digest generation for a user (for testing/debugging).
    
    Args:
        user_id: User ID to generate digest for
    
    Returns:
        True if successful
    """
    db = SessionLocal()
    try:
        return generate_digest_for_user(user_id, db)
    finally:
        db.close()

