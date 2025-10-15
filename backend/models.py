"""SQLAlchemy database models for the News Agent application."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User model for authentication and preferences."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    digests = relationship("NewsDigest", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class UserPreferences(Base):
    """User preferences for location and notification settings."""
    
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Location settings (supports multiple locations as JSON)
    primary_location = Column(String(500), nullable=True)
    additional_locations = Column(JSON, default=list)  # List of additional locations
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    notification_time = Column(String(5), default="07:00")  # Format: "HH:MM" in user's local time
    timezone = Column(String(50), default="UTC")  # e.g., "America/New_York", "Australia/Melbourne"
    
    # Content preferences
    severity_threshold = Column(String(20), default="all")  # "all", "medium", "high"
    radius_km = Column(Integer, default=5)  # Search radius in kilometers
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, location='{self.primary_location}')>"


class NewsDigest(Base):
    """Daily news digest for a user."""
    
    __tablename__ = "news_digests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Digest metadata
    location = Column(String(500), nullable=False)
    digest_date = Column(DateTime(timezone=True), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Digest content
    articles = Column(JSON, nullable=False)  # List of article dicts with title, summary, url, source
    summary_text = Column(Text, nullable=True)  # Overall digest summary from digest_agent
    
    # Email delivery tracking
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    email_opened = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="digests")
    
    def __repr__(self):
        return f"<NewsDigest(id={self.id}, user_id={self.user_id}, date={self.digest_date})>"


class NewsArticle(Base):
    """Individual news articles cached for deduplication and reference."""
    
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Article metadata
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, index=True, nullable=False)
    source = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Article content
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Location and relevance
    location = Column(String(500), nullable=True)
    incident_type = Column(String(100), nullable=True)  # e.g., "theft", "burglary", "assault"
    severity_score = Column(Integer, default=0)  # 0-100 scale
    
    # Geocoding
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...')>"

