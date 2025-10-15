"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRegister(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: Optional[int] = None


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# User Preferences Schemas
# ============================================================================

class UserPreferencesBase(BaseModel):
    """Base preferences schema."""
    primary_location: Optional[str] = Field(None, max_length=500)
    additional_locations: Optional[List[str]] = Field(default_factory=list)
    email_notifications: Optional[bool] = True
    notification_time: Optional[str] = Field("07:00", pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = Field("UTC", max_length=50)
    severity_threshold: Optional[str] = Field("all", pattern=r"^(all|medium|high)$")
    radius_km: Optional[int] = Field(5, ge=1, le=100)


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences."""
    pass


class UserPreferencesUpdate(UserPreferencesBase):
    """Schema for updating user preferences."""
    pass


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response."""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# News Article Schemas
# ============================================================================

class NewsArticleBase(BaseModel):
    """Base news article schema."""
    title: str
    url: str
    source: Optional[str] = None
    summary: Optional[str] = None
    incident_type: Optional[str] = None
    severity_score: Optional[int] = Field(0, ge=0, le=100)


class NewsArticleResponse(NewsArticleBase):
    """Schema for news article response."""
    id: int
    published_at: Optional[datetime] = None
    location: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# News Digest Schemas
# ============================================================================

class NewsDigestRequest(BaseModel):
    """Schema for requesting a news digest."""
    location: Optional[str] = Field(None, max_length=500)
    date: Optional[datetime] = None


class ArticleDict(BaseModel):
    """Schema for article dictionary in digest."""
    title: str
    summary: str
    url: str
    source: str
    published_at: Optional[str] = None
    severity_score: Optional[int] = 0


class NewsDigestResponse(BaseModel):
    """Schema for news digest response."""
    id: int
    user_id: int
    location: str
    digest_date: datetime
    generated_at: datetime
    articles: List[dict]
    summary_text: Optional[str] = None
    email_sent: bool
    
    class Config:
        from_attributes = True


class NewsDigestListResponse(BaseModel):
    """Schema for list of news digests."""
    digests: List[NewsDigestResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# General Response Schemas
# ============================================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    code: Optional[str] = None

