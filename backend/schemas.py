"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, HttpUrl


# ========== Auth Schemas ==========
class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=2, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User information response."""

    id: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Business Schemas ==========
class PlanType(str, Enum):
    """Subscription plan types."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BusinessCreate(BaseModel):
    """Schema for creating a new business."""

    name: str = Field(min_length=2, max_length=255)
    website: HttpUrl | None = None
    description: str | None = Field(None, max_length=2000)


class BusinessUpdate(BaseModel):
    """Schema for updating business details."""

    name: str | None = Field(None, min_length=2, max_length=255)
    website: HttpUrl | None = None
    description: str | None = Field(None, max_length=2000)
    bot_name: str | None = Field(None, min_length=1, max_length=100)
    welcome_message: str | None = Field(None, max_length=500)
    theme_color: str | None = Field(None, pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$")


class BusinessResponse(BaseModel):
    """Business information response."""

    id: str
    name: str
    website: str | None
    description: str | None
    bot_name: str
    welcome_message: str
    theme_color: str
    plan: PlanType
    queries_this_month: int
    total_queries: int
    document_count: int
    is_active: bool
    created_at: datetime
    api_key: str

    class Config:
        from_attributes = True


class WidgetConfig(BaseModel):
    """Widget configuration for embedding."""

    business_id: str
    bot_name: str
    welcome_message: str
    theme_color: str
    api_endpoint: str


# ========== Document Schemas ==========
class DocumentResponse(BaseModel):
    """Document information response."""

    id: str
    business_id: str
    filename: str
    file_size: int
    file_type: str
    is_processed: bool
    chunks_count: int
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""

    documents: list[DocumentResponse]
    message: str


class URLIngestRequest(BaseModel):
    """Request to ingest website URLs."""

    urls: list[HttpUrl] = Field(min_length=1, max_length=10)


# ========== Chat Schemas ==========
class ChatRequest(BaseModel):
    """Chat message request."""

    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat message response."""

    answer: str
    business_id: str
    session_id: str
    response_time_ms: int
    sources_count: int


class FeedbackRequest(BaseModel):
    """User feedback on bot response."""

    conversation_id: str
    feedback: int = Field(ge=-1, le=1)  # -1: bad, 0: neutral, 1: good


# ========== Analytics Schemas ==========
class AnalyticsResponse(BaseModel):
    """Business analytics summary."""

    total_queries: int
    queries_today: int
    queries_this_month: int
    unique_sessions_today: int
    avg_response_time_ms: float
    satisfaction_rate: float
    top_questions: list[tuple[str, int]]


class ConversationResponse(BaseModel):
    """Conversation/chat log response."""

    id: str
    session_id: str
    user_message: str
    bot_response: str
    response_time_ms: int
    was_answered: bool
    user_feedback: int | None
    created_at: datetime

    class Config:
        from_attributes = True


# ========== General Schemas ==========
class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    version: str
    ollama_status: str
    database_status: str


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    error_code: str | None = None
