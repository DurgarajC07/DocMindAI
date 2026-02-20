"""Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any

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


# ========== Agent Configuration Schemas ==========
class AgentPersonality(str, Enum):
    """Agent personality types."""
    
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    TECHNICAL = "technical"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    ENTHUSIASTIC = "enthusiastic"


class BusinessCategory(str, Enum):
    """Business category for template selection."""
    
    ECOMMERCE = "ecommerce"
    SAAS = "saas"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    LEGAL = "legal"
    HOSPITALITY = "hospitality"
    REAL_ESTATE = "real_estate"
    RESTAURANT = "restaurant"
    CONSULTING = "consulting"
    CUSTOM = "custom"


class ResponseTone(str, Enum):
    """Response tone options."""
    
    FORMAL = "formal"
    CONVERSATIONAL = "conversational"
    CONCISE = "concise"
    DETAILED = "detailed"


class AgentConfigUpdate(BaseModel):
    """Update agent configuration."""
    
    agent_personality: AgentPersonality | None = None
    business_category: BusinessCategory | None = None
    system_prompt: str | None = Field(None, max_length=5000)
    response_tone: ResponseTone | None = None
    use_hybrid_search: bool | None = None
    use_reranking: bool | None = None
    chunk_size: int | None = Field(None, ge=100, le=5000)
    chunk_overlap: int | None = Field(None, ge=0, le=1000)


class AgentConfigResponse(BaseModel):
    """Agent configuration response."""
    
    business_id: str
    agent_personality: str
    business_category: str
    system_prompt: str | None
    response_tone: str
    use_hybrid_search: bool
    use_reranking: bool
    chunk_size: int
    chunk_overlap: int
    
    class Config:
        from_attributes = True


class PromptAnalysisRequest(BaseModel):
    """Request to analyze a prompt."""
    
    prompt: str = Field(min_length=10, max_length=5000)


class PromptAnalysisResponse(BaseModel):
    """Prompt analysis result."""
    
    score: int
    quality: str
    issues: list[str]
    suggestions: list[str]
    word_count: int


class PromptImprovementRequest(BaseModel):
    """Request to improve a prompt."""
    
    rough_prompt: str = Field(min_length=5, max_length=1000)
    business_type: str = "general"


class PromptImprovementResponse(BaseModel):
    """Improved prompt response."""
    
    original_prompt: str
    improved_prompt: str
    suggestions: list[str]


class TemplateRequest(BaseModel):
    """Request to get/apply a template."""
    
    category: BusinessCategory
    business_name: str = Field(min_length=2, max_length=255)
    custom_guidelines: str | None = Field(None, max_length=2000)


class TemplateResponse(BaseModel):
    """Template configuration response."""
    
    name: str
    category: str
    personality: str
    system_prompt: str
    welcome_message: str
    sample_questions: list[str]
    response_tone: str


class WelcomeMessageSuggestions(BaseModel):
    """Welcome message suggestions."""
    
    suggestions: list[str]


class ContentFilterConfig(BaseModel):
    """Content filter configuration."""
    
    block_profanity: bool = True
    block_personal_info_requests: bool = True
    block_competitor_mentions: bool = False
    max_response_length: int = Field(default=500, ge=100, le=2000)
    allowed_topics: list[str] = []
    blocked_topics: list[str] = []


class AgentRestrictionsConfig(BaseModel):
    """Agent behavioral restrictions."""
    
    cannot_make_purchases: bool = True
    cannot_modify_account: bool = True
    cannot_access_personal_data: bool = True
    must_stay_on_topic: bool = True
    must_cite_sources: bool = False
    must_admit_uncertainty: bool = True
    require_human_handoff: list[str] = []


class PromptTemplateCreate(BaseModel):
    """Create a prompt template."""
    
    name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=50)
    system_prompt: str = Field(min_length=10, max_length=5000)
    welcome_message: str = Field(min_length=5, max_length=500)
    is_public: bool = False


class PromptTemplateResponse(BaseModel):
    """Prompt template response."""
    
    id: str
    user_id: str
    name: str
    category: str
    system_prompt: str
    welcome_message: str
    is_public: bool
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UploadProgressResponse(BaseModel):
    """Upload progress status."""
    
    upload_id: str
    filename: str
    total_size: int
    uploaded_size: int
    progress: float
    status: str
    error: str | None = None


class RAGEngineStats(BaseModel):
    """RAG engine statistics."""
    
    business_id: str
    total_chunks: int
    cached_responses: int
    active_sessions: int
    hybrid_search_enabled: bool
    reranking_enabled: bool
