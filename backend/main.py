"""Main FastAPI application."""

import uuid
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path
from typing import Annotated

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import (
    authenticate_user,
    create_access_token,
    get_business_by_api_key,
    get_current_active_user,
    get_password_hash,
    get_user_business,
)
from backend.config import get_settings
from backend.database import (
    Business,
    Conversation,
    Document,
    User,
    get_db,
    init_db,
    PromptTemplate,
    AgentConfigHistory,
    ConversationSession,
)
from backend.advanced_rag import get_advanced_rag_engine
from backend.agent_config import (
    PromptAssistant,
    get_template,
    customize_template,
    validate_response_against_filters,
    AGENT_TEMPLATES,
)
from backend.file_handler import handle_large_file_upload, progress_tracker
from backend.rag_engine import get_rag_engine
from backend.rate_limiter import check_and_increment_rate_limit, rate_limiter
from backend.schemas import (
    AnalyticsResponse,
    BusinessCreate,
    BusinessResponse,
    BusinessUpdate,
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    DocumentResponse,
    DocumentUploadResponse,
    FeedbackRequest,
    HealthCheck,
    Token,
    URLIngestRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    WidgetConfig,
    AgentConfigUpdate,
    AgentConfigResponse,
    PromptAnalysisRequest,
    PromptAnalysisResponse,
    PromptImprovementRequest,
    PromptImprovementResponse,
    TemplateRequest,
    TemplateResponse,
    WelcomeMessageSuggestions,
    ContentFilterConfig,
    AgentRestrictionsConfig,
    PromptTemplateCreate,
    PromptTemplateResponse,
    UploadProgressResponse,
    RAGEngineStats,
    BusinessCategory,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting DocMind AI application...")
    await init_db()
    await rate_limiter.connect()
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await rate_limiter.disconnect()
    logger.info("Application shut down complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Health Check ==========
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    # Check Ollama
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
            ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        ollama_status = "unavailable"
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "ollama_status": ollama_status,
        "database_status": "healthy",
    }


# ========== Authentication Routes ==========
@app.post("/api/v1/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user."""
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"New user registered: {user.email}")
    return user


@app.post("/api/v1/auth/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login and get access token."""
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    
    logger.info(f"User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current user information."""
    return current_user


# ========== Business Routes ==========
@app.post("/api/v1/businesses", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_data: BusinessCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new business/chatbot."""
    business = Business(
        owner_id=current_user.id,
        name=business_data.name,
        website=str(business_data.website) if business_data.website else None,
        description=business_data.description,
    )
    db.add(business)
    await db.commit()
    await db.refresh(business)
    
    logger.info(f"New business created: {business.name} (ID: {business.id})")
    return business


@app.get("/api/v1/businesses", response_model=list[BusinessResponse])
async def list_businesses(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all businesses owned by current user."""
    result = await db.execute(
        select(Business).where(Business.owner_id == current_user.id)
    )
    businesses = result.scalars().all()
    return list(businesses)


@app.get("/api/v1/businesses/{business_id}", response_model=BusinessResponse)
async def get_business(
    business: Annotated[Business, Depends(get_user_business)],
):
    """Get a specific business."""
    return business


@app.patch("/api/v1/businesses/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_data: BusinessUpdate,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update business details."""
    update_data = business_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if value is not None:
            if field == "website" and value:
                value = str(value)
            setattr(business, field, value)
    
    await db.commit()
    await db.refresh(business)
    
    logger.info(f"Business updated: {business.id}")
    return business


@app.delete("/api/v1/businesses/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a business and all its data."""
    # Delete vector store collection
    rag_engine = get_rag_engine(business.id)
    await rag_engine.delete_collection()
    
    # Delete business from database (cascade will delete documents and conversations)
    await db.delete(business)
    await db.commit()
    
    logger.info(f"Business deleted: {business.id}")
    return None


@app.post("/api/v1/businesses/{business_id}/regenerate-key")
async def regenerate_api_key(
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Regenerate API key for a business."""
    business.api_key = str(uuid.uuid4())
    await db.commit()
    await db.refresh(business)
    
    logger.info(f"API key regenerated for business: {business.id}")
    return {"api_key": business.api_key, "business_id": business.id}


@app.patch("/api/v1/businesses/{business_id}/widget-config")
async def update_widget_config(
    config_data: dict,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update widget configuration."""
    if "bot_name" in config_data:
        business.bot_name = config_data["bot_name"]
    if "welcome_message" in config_data:
        business.welcome_message = config_data["welcome_message"]
    if "theme_color" in config_data:
        business.theme_color = config_data["theme_color"]
    
    await db.commit()
    await db.refresh(business)
    
    logger.info(f"Widget config updated for business: {business.id}")
    return {
        "business_id": business.id,
        "bot_name": business.bot_name,
        "welcome_message": business.welcome_message,
        "theme_color": business.theme_color,
    }


# ========== Document Routes ==========
async def process_document_background(
    doc_id: str,
    file_path: Path,
    file_ext: str,
    business_id: str,
):
    """Process document in background with detailed logging."""
    from backend.database import AsyncSessionLocal
    from backend.rag_engine import RAGEngine
    
    logger.info(f"📄 Starting background processing for document {doc_id}")
    logger.info(f"   File: {file_path}, Type: {file_ext}, Business: {business_id}")
    
    rag_engine = RAGEngine(business_id=business_id)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get document
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"❌ Document {doc_id} not found in database")
                return
            
            logger.info(f"🔍 Processing file: {doc.filename}")
            
            # Process based on file type
            if file_ext == ".pdf":
                logger.info(f"📕 Ingesting PDF document...")
                result = await rag_engine.ingest_pdf(file_path)
            elif file_ext in [".txt", ".html"]:
                logger.info(f"📝 Ingesting text document...")
                result = await rag_engine.ingest_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Update document
            doc.is_processed = True
            doc.chunks_count = result["chunks_count"]
            
            logger.info(f"✅ Document chunked into {result['chunks_count']} pieces")
            
            # Update business
            business_result = await db.execute(
                select(Business).where(Business.id == business_id)
            )
            business = business_result.scalar_one_or_none()
            if business:
                business.document_count += 1
            
            await db.commit()
            logger.info(f"✅ Document {doc_id} ({doc.filename}) processing COMPLETE!")
            logger.info(f"   Total chunks: {result['chunks_count']}")
            logger.info(f"   Status: Ready for queries")
            
        except Exception as e:
            # Update error
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.error_message = str(e)
                await db.commit()
            logger.error(f"❌ Failed to process document {doc_id}: {e}")
            logger.exception("Full error traceback:")


@app.post("/api/v1/businesses/{business_id}/documents", response_model=DocumentUploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
    files: list[UploadFile] = File(...),
):
    """Upload documents and process them in background."""
    # Check document limit
    await rate_limiter.check_document_limit(business, db)
    
    upload_dir = settings.upload_dir / business.id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_docs = []
    limits = settings.get_plan_limits(business.plan.value)
    
    for file in files:
        # Validate file extension
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in settings.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_ext} not allowed. Allowed: {', '.join(settings.allowed_extensions)}",
            )
        
        # Read and validate file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > limits["max_document_size"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File {file.filename} size ({file_size} bytes) exceeds plan limit ({limits['max_document_size']} bytes)",
            )
        
        # Save file
        file_path = upload_dir / f"{uuid.uuid4()}_{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create document record
        doc = Document(
            business_id=business.id,
            filename=file.filename or "unknown",
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_ext,
            is_processed=False,  # Will be updated by background task
        )
        db.add(doc)
        await db.flush()  # Get the document ID
        
        # Schedule background processing
        background_tasks.add_task(
            process_document_background,
            doc.id,
            file_path,
            file_ext,
            business.id,
        )
        
        uploaded_docs.append(doc)
        logger.info(f"📤 File uploaded: {file.filename} ({file_size} bytes)")
        logger.info(f"   Document ID: {doc.id}")
        logger.info(f"   Status: Queued for processing")
        logger.info(f"   Check status: GET /api/v1/businesses/{business.id}/documents/{doc.id}")
    
    await db.commit()
    
    for doc in uploaded_docs:
        await db.refresh(doc)
    
    logger.info(f"=" * 60)
    logger.info(f"📊 Upload Summary:")
    logger.info(f"   Total files: {len(uploaded_docs)}")
    logger.info(f"   Business: {business.name} ({business.id})")
    logger.info(f"   Status: Processing in background")
    logger.info(f"   Track progress: GET /api/v1/businesses/{business.id}/documents")
    logger.info(f"=" * 60)
    
    return {
        "documents": uploaded_docs,
        "message": f"Successfully uploaded {len(uploaded_docs)} document(s). Processing in background. Check document status to see when chunking is complete.",
    }


@app.post("/api/v1/businesses/{business_id}/documents/text", response_model=DocumentUploadResponse)
async def ingest_text(
    text_data: dict,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Ingest text content directly."""
    # Check document limit
    await rate_limiter.check_document_limit(business, db)
    
    rag_engine = get_rag_engine(business.id)
    
    text_content = text_data.get("text", "")
    if not text_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required",
        )
    
    # Create temporary file for text
    temp_dir = Path("uploads") / str(business.id)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / f"text_{uuid.uuid4()}.txt"
    
    temp_file.write_text(text_content)
    
    logger.info(f"📝 Ingesting direct text input ({len(text_content)} characters)")
    
    # Create document record
    doc = Document(
        business_id=business.id,
        filename="Direct Text Input",
        file_path=str(temp_file),
        file_size=len(text_content),
        file_type=".txt",
    )
    db.add(doc)
    
    # Process text
    try:
        result = await rag_engine.ingest_text(temp_file)
        doc.is_processed = True
        doc.chunks_count = result["chunks_count"]
        business.document_count += 1
        logger.info(f"✅ Text ingestion complete: {result['chunks_count']} chunks created")
    except Exception as e:
        doc.error_message = str(e)
        logger.error(f"❌ Failed to process text content: {e}")
    
    await db.commit()
    await db.refresh(doc)
    
    return {
        "documents": [doc],
        "message": f"Text content ingested successfully ({doc.chunks_count} chunks)" if doc.is_processed else "Text ingestion failed",
    }


@app.post("/api/v1/businesses/{business_id}/documents/urls", response_model=DocumentUploadResponse)
async def ingest_urls(
    url_data: URLIngestRequest,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Ingest content from URLs."""
    # Check document limit
    await rate_limiter.check_document_limit(business, db)
    
    logger.info(f"🌐 Ingesting {len(url_data.urls)} URL(s)")
    
    rag_engine = get_rag_engine(business.id)
    ingested_docs = []
    
    for url in url_data.urls:
        url_str = str(url)
        
        logger.info(f"🔗 Processing URL: {url_str}")
        
        # Create document record
        doc = Document(
            business_id=business.id,
            filename=url_str,
            file_path=url_str,
            file_size=0,
            file_type="url",
        )
        db.add(doc)
        
        # Process URL
        try:
            result = await rag_engine.ingest_url(url_str)
            doc.is_processed = True
            doc.chunks_count = result["chunks_count"]
            business.document_count += 1
            logger.info(f"✅ URL ingested: {url_str} ({result['chunks_count']} chunks)")
        except Exception as e:
            doc.error_message = str(e)
            logger.error(f"❌ Failed to process URL {url_str}: {e}")
        
        ingested_docs.append(doc)
    
    await db.commit()
    
    for doc in ingested_docs:
        await db.refresh(doc)
    
    successful = sum(1 for doc in ingested_docs if doc.is_processed)
    logger.info(f"📊 URL ingestion complete: {successful}/{len(ingested_docs)} successful")
    
    return {
        "documents": ingested_docs,
        "message": f"Successfully ingested {successful}/{len(ingested_docs)} URL(s)",
    }


@app.get("/api/v1/businesses/{business_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all documents for a business."""
    result = await db.execute(
        select(Document).where(Document.business_id == business.id).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()
    return list(documents)


@app.get("/api/v1/businesses/{business_id}/documents/{document_id}", response_model=DocumentResponse)
async def get_document_status(
    document_id: str,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Get document processing status.
    Use this to check if chunking is complete.
    
    Response fields:
    - is_processed: True if chunking is complete
    - chunks_count: Number of chunks created (only if processed)
    - error_message: Error details if processing failed
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.business_id == business.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Log current status
    if document.is_processed:
        logger.info(f"✅ Document {document_id} status: COMPLETE ({document.chunks_count} chunks)")
    elif document.error_message:
        logger.warning(f"❌ Document {document_id} status: FAILED - {document.error_message}")
    else:
        logger.info(f"⏳ Document {document_id} status: PROCESSING...")
    
    return document


@app.delete("/api/v1/businesses/{business_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.business_id == business.id,
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    # Delete file if it exists
    if document.file_type != "url":
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()
    
    await db.delete(document)
    business.document_count = max(0, business.document_count - 1)
    await db.commit()
    
    logger.info(f"Document deleted: {document_id}")
    return None


# ========== Chat Routes ==========
@app.post("/api/v1/chat/{business_id}", response_model=ChatResponse)
async def chat(
    business_id: str,
    chat_request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Public chat endpoint for widget (no authentication required, only business_id)."""
    # Get business
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.is_active == True)
    )
    business = result.scalar_one_or_none()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    # Check rate limits
    await rate_limiter.check_rate_limit(business, db)
    
    # Generate session ID if not provided
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    # Get answer from RAG engine
    rag_engine = get_rag_engine(business_id)
    answer, response_time_ms, sources_count = await rag_engine.ask(chat_request.question)
    
    # Log conversation
    conversation = Conversation(
        business_id=business_id,
        session_id=session_id,
        user_message=chat_request.question,
        bot_response=answer,
        response_time_ms=response_time_ms,
        sources_used=sources_count,
        was_answered=sources_count > 0,
    )
    db.add(conversation)
    
    # Increment usage
    await rate_limiter.increment_usage(business, db)
    
    await db.commit()
    
    return {
        "answer": answer,
        "business_id": business_id,
        "session_id": session_id,
        "response_time_ms": response_time_ms,
        "sources_count": sources_count,
    }


@app.get("/api/v1/businesses/{business_id}/widget-config", response_model=WidgetConfig)
async def get_widget_config(business_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Get widget configuration (public endpoint)."""
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.is_active == True)
    )
    business = result.scalar_one_or_none()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    return {
        "business_id": business.id,
        "bot_name": business.bot_name,
        "welcome_message": business.welcome_message,
        "theme_color": business.theme_color,
        "api_endpoint": f"{settings.api_v1_prefix}/chat/{business.id}",
    }


# ========== Analytics Routes ==========
@app.get("/api/v1/businesses/{business_id}/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get analytics for a business."""
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    
    # Queries today
    result = await db.execute(
        select(func.count(Conversation.id))
        .where(
            Conversation.business_id == business.id,
            func.date(Conversation.created_at) == today,
        )
    )
    queries_today = result.scalar_one()
    
    # Unique sessions today
    result = await db.execute(
        select(func.count(func.distinct(Conversation.session_id)))
        .where(
            Conversation.business_id == business.id,
            func.date(Conversation.created_at) == today,
        )
    )
    unique_sessions_today = result.scalar_one()
    
    # Average response time
    result = await db.execute(
        select(func.avg(Conversation.response_time_ms))
        .where(Conversation.business_id == business.id)
    )
    avg_response_time = result.scalar_one() or 0.0
    
    # Satisfaction rate (based on feedback)
    result = await db.execute(
        select(
            func.count(Conversation.id),
            func.sum(func.case((Conversation.user_feedback == 1, 1), else_=0)),
        )
        .where(
            Conversation.business_id == business.id,
            Conversation.user_feedback.isnot(None),
        )
    )
    total_feedback, positive_feedback = result.one()
    satisfaction_rate = (positive_feedback / total_feedback * 100) if total_feedback else 0.0
    
    # Top questions (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    result = await db.execute(
        select(
            Conversation.user_message,
            func.count(Conversation.id).label("count"),
        )
        .where(
            Conversation.business_id == business.id,
            Conversation.created_at >= thirty_days_ago,
        )
        .group_by(Conversation.user_message)
        .order_by(func.count(Conversation.id).desc())
        .limit(10)
    )
    top_questions = [(row.user_message, row.count) for row in result]
    
    return {
        "total_queries": business.total_queries,
        "queries_today": queries_today,
        "queries_this_month": business.queries_this_month,
        "unique_sessions_today": unique_sessions_today,
        "avg_response_time_ms": float(avg_response_time),
        "satisfaction_rate": float(satisfaction_rate),
        "top_questions": top_questions,
    }


@app.get("/api/v1/businesses/{business_id}/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
):
    """List recent conversations."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.business_id == business.id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    conversations = result.scalars().all()
    return list(conversations)


@app.post("/api/v1/conversations/{conversation_id}/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    conversation_id: str,
    feedback_data: FeedbackRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit feedback for a conversation (public endpoint)."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    conversation.user_feedback = feedback_data.feedback
    await db.commit()
    
    return None


# ========== Widget Static Files ==========
@app.get("/widget.js")
async def get_widget_script():
    """Serve the widget JavaScript file."""
    widget_path = Path(__file__).parent.parent / "widget" / "widget.js"
    if not widget_path.exists():
        raise HTTPException(status_code=404, detail="Widget script not found")
    return FileResponse(widget_path, media_type="application/javascript")


# ========== Agent Configuration Endpoints ==========

@app.get("/api/v1/businesses/{business_id}/agent-config", response_model=AgentConfigResponse)
async def get_agent_config(
    business: Annotated[Business, Depends(get_user_business)],
):
    """Get agent configuration for a business."""
    return {
        "business_id": business.id,
        "agent_personality": business.agent_personality,
        "business_category": business.business_category,
        "system_prompt": business.system_prompt,
        "response_tone": business.response_tone,
        "use_hybrid_search": business.use_hybrid_search,
        "use_reranking": business.use_reranking,
        "chunk_size": business.chunk_size,
        "chunk_overlap": business.chunk_overlap,
    }


@app.patch("/api/v1/businesses/{business_id}/agent-config", response_model=AgentConfigResponse)
async def update_agent_config(
    config_data: AgentConfigUpdate,
    business: Annotated[Business, Depends(get_user_business)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update agent configuration."""
    update_data = config_data.model_dump(exclude_unset=True)
    
    # Track changes for history
    for field, new_value in update_data.items():
        old_value = getattr(business, field, None)
        if old_value != new_value:
            # Log change
            history = AgentConfigHistory(
                business_id=business.id,
                changed_by=current_user.id,
                field_name=field,
                old_value=str(old_value) if old_value else None,
                new_value=str(new_value) if new_value else None,
            )
            db.add(history)
            
            # Update business
            setattr(business, field, new_value)
    
    await db.commit()
    await db.refresh(business)
    
    # Clear RAG cache if search settings changed
    if any(k in update_data for k in ["use_hybrid_search", "use_reranking", "chunk_size", "chunk_overlap"]):
        from backend.advanced_rag import clear_rag_cache
        clear_rag_cache()
    
    logger.info(f"Agent config updated for business: {business.id}")
    
    return {
        "business_id": business.id,
        "agent_personality": business.agent_personality,
        "business_category": business.business_category,
        "system_prompt": business.system_prompt,
        "response_tone": business.response_tone,
        "use_hybrid_search": business.use_hybrid_search,
        "use_reranking": business.use_reranking,
        "chunk_size": business.chunk_size,
        "chunk_overlap": business.chunk_overlap,
    }


# ========== Template Endpoints ==========
# NOTE: Specific routes MUST come before parameterized routes

@app.get("/api/v1/templates/categories")
async def list_template_categories():
    """List available template categories."""
    return {
        "categories": [
            {"value": cat.value, "label": cat.value.replace("_", " ").title()}
            for cat in BusinessCategory
        ]
    }


@app.get("/api/v1/templates/welcome-suggestions", response_model=WelcomeMessageSuggestions)
async def get_welcome_suggestions(
    business_name: str,
    category: BusinessCategory = BusinessCategory.CUSTOM,
):
    """Get welcome message suggestions."""
    suggestions = PromptAssistant.generate_welcome_messages(business_name, category)
    return {"suggestions": suggestions}


@app.get("/api/v1/templates/{category}", response_model=TemplateResponse)
async def get_template_by_category(category: BusinessCategory):
    """Get template for a specific category."""
    template = get_template(category)
    
    return {
        "name": template.name,
        "category": template.category.value,
        "personality": template.personality.value,
        "system_prompt": template.system_prompt,
        "welcome_message": template.welcome_message,
        "sample_questions": template.sample_questions,
        "response_tone": template.response_tone.value,
    }


@app.post("/api/v1/businesses/{business_id}/apply-template")
async def apply_template(
    template_request: TemplateRequest,
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Apply a template to a business."""
    # Get base template
    template = get_template(template_request.category)
    
    # Customize for business
    customized = customize_template(
        template,
        template_request.business_name,
        template_request.custom_guidelines,
    )
    
    # Update business
    business.business_category = customized.category.value
    business.agent_personality = customized.personality.value
    business.system_prompt = customized.system_prompt
    business.welcome_message = customized.welcome_message
    business.response_tone = customized.response_tone.value
    business.bot_name = customized.name
    
    await db.commit()
    
    logger.info(f"Applied template {template_request.category} to business {business.id}")
    
    return {
        "message": "Template applied successfully",
        "template_name": customized.name,
        "category": customized.category.value,
    }


# ========== Prompt Assistant Endpoints ==========

@app.post("/api/v1/prompt-assistant/analyze", response_model=PromptAnalysisResponse)
async def analyze_prompt(request: PromptAnalysisRequest):
    """Analyze a prompt and provide feedback."""
    analysis = PromptAssistant.analyze_prompt(request.prompt)
    return analysis


@app.post("/api/v1/prompt-assistant/improve", response_model=PromptImprovementResponse)
async def improve_prompt(request: PromptImprovementRequest):
    """Improve a rough prompt."""
    improved = PromptAssistant.improve_prompt(
        request.rough_prompt,
        request.business_type,
    )
    
    return {
        "original_prompt": request.rough_prompt,
        "improved_prompt": improved,
        "suggestions": [
            "Review and customize the improved prompt",
            "Test it with sample questions",
            "Adjust tone and personality as needed",
        ],
    }


@app.get("/api/v1/prompt-assistant/samples")
async def get_sample_prompts(category: BusinessCategory = BusinessCategory.CUSTOM):
    """Get sample prompts for a category."""
    samples = PromptAssistant.get_sample_prompts(category)
    return {"samples": samples, "category": category.value}


# ========== Prompt Template Management ==========

@app.post("/api/v1/prompt-templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
    template_data: PromptTemplateCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Save a prompt template for reuse."""
    template = PromptTemplate(
        user_id=current_user.id,
        name=template_data.name,
        category=template_data.category,
        system_prompt=template_data.system_prompt,
        welcome_message=template_data.welcome_message,
        is_public=template_data.is_public,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    
    logger.info(f"Created prompt template: {template.name}")
    return template


@app.get("/api/v1/prompt-templates", response_model=list[PromptTemplateResponse])
async def list_prompt_templates(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_public: bool = True,
):
    """List user's prompt templates."""
    # Get user's templates
    query = select(PromptTemplate).where(PromptTemplate.user_id == current_user.id)
    
    if include_public:
        # Also include public templates
        query = select(PromptTemplate).where(
            (PromptTemplate.user_id == current_user.id) | (PromptTemplate.is_public == True)
        )
    
    result = await db.execute(query.order_by(PromptTemplate.created_at.desc()))
    templates = result.scalars().all()
    
    return list(templates)


@app.get("/api/v1/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific prompt template."""
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == template_id,
            (PromptTemplate.user_id == current_user.id) | (PromptTemplate.is_public == True)
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    
    # Increment usage count
    template.usage_count += 1
    await db.commit()
    
    return template


@app.delete("/api/v1/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a prompt template."""
    result = await db.execute(
        select(PromptTemplate).where(
            PromptTemplate.id == template_id,
            PromptTemplate.user_id == current_user.id,
        )
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )
    
    await db.delete(template)
    await db.commit()
    
    return {"message": "Template deleted successfully"}


# ========== Upload Progress Endpoint ==========

@app.get("/api/v1/uploads/{upload_id}/progress", response_model=UploadProgressResponse)
async def get_upload_progress(upload_id: str):
    """Get upload progress for a file."""
    progress = progress_tracker.get_progress(upload_id)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found",
        )
    
    return {
        "upload_id": upload_id,
        **progress,
    }


# ========== RAG Engine Stats ==========

@app.get("/api/v1/businesses/{business_id}/rag-stats", response_model=RAGEngineStats)
async def get_rag_stats(
    business: Annotated[Business, Depends(get_user_business)],
):
    """Get RAG engine statistics."""
    rag_engine = get_advanced_rag_engine(business.id)
    stats = rag_engine.get_stats()
    return stats


@app.post("/api/v1/businesses/{business_id}/rag-cache/clear")
async def clear_rag_cache_endpoint(
    business: Annotated[Business, Depends(get_user_business)],
):
    """Clear RAG cache for a business."""
    rag_engine = get_advanced_rag_engine(business.id)
    rag_engine.clear_cache()
    
    return {"message": "RAG cache cleared successfully"}


# ========== Enhanced Chat Endpoint with Advanced RAG ==========

@app.post("/api/v1/chat/{business_id}/advanced", response_model=ChatResponse)
async def chat_advanced(
    business_id: str,
    chat_request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    use_context: bool = True,
):
    """Advanced chat endpoint using optimized RAG engine with hybrid search and re-ranking."""
    # Get business
    result = await db.execute(
        select(Business).where(Business.id == business_id, Business.is_active == True)
    )
    business = result.scalar_one_or_none()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    
    # Check rate limits
    await rate_limiter.check_rate_limit(business, db)
    
    # Generate session ID
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    # Get advanced RAG engine
    rag_engine = get_advanced_rag_engine(business_id)
    
    # Get answer with all optimizations
    answer, response_time_ms, sources_count = await rag_engine.ask(
        question=chat_request.question,
        session_id=session_id,
        use_context=use_context,
        system_prompt=business.system_prompt,
    )
    
    # Validate response against filters if configured
    if business.content_filter_rules:
        import json
        try:
            filter_config = json.loads(business.content_filter_rules)
            from backend.agent_config import ContentFilter
            filters = ContentFilter(**filter_config)
            
            is_valid, reason = validate_response_against_filters(answer, filters)
            if not is_valid:
                answer = "I apologize, but I cannot provide that response. Please rephrase your question."
                logger.warning(f"Response filtered: {reason}")
        except Exception as e:
            logger.error(f"Filter validation failed: {e}")
    
    # Log conversation
    conversation = Conversation(
        business_id=business_id,
        session_id=session_id,
        user_message=chat_request.question,
        bot_response=answer,
        response_time_ms=response_time_ms,
        sources_used=sources_count,
        was_answered=sources_count > 0,
    )
    db.add(conversation)
    
    # Update session
    result = await db.execute(
        select(ConversationSession).where(ConversationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        session = ConversationSession(
            id=session_id,
            business_id=business_id,
            total_messages=1,
            avg_response_time=response_time_ms,
        )
        db.add(session)
    else:
        session.total_messages += 1
        # Update average response time
        session.avg_response_time = (
            (session.avg_response_time * (session.total_messages - 1) + response_time_ms)
            // session.total_messages
        )
    
    # Increment usage
    await rate_limiter.increment_usage(business, db)
    
    await db.commit()
    
    return {
        "answer": answer,
        "business_id": business_id,
        "session_id": session_id,
        "response_time_ms": response_time_ms,
        "sources_count": sources_count,
    }


# ========== Enhanced Document Upload with Streaming ==========

@app.post("/api/v1/businesses/{business_id}/documents/upload-large")
async def upload_large_document(
    business: Annotated[Business, Depends(get_user_business)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    """Upload large files with streaming and progress tracking."""
    # Check document limit
    await rate_limiter.check_document_limit(business, db)
    
    # Get plan limits
    limits = settings.get_plan_limits(business.plan.value)
    upload_dir = settings.upload_dir / business.id
    
    # Handle file upload with streaming
    file_info = await handle_large_file_upload(
        file=file,
        business_id=business.id,
        upload_dir=upload_dir,
        max_size=limits["max_document_size"],
    )
    
    # Create document record
    import json
    doc = Document(
        business_id=business.id,
        filename=file_info["filename"],
        file_path=file_info["file_path"],
        file_size=file_info["file_size"],
        file_type=Path(file_info["filename"]).suffix,
        content_hash=file_info["content_hash"],
        metadata_json=json.dumps({
            "mime_type": file_info["mime_type"],
            "upload_id": file_info["upload_id"],
        }),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    logger.info(f"Large file uploaded: {file.filename} ({file_info['file_size']} bytes)")
    
    return {
        "document": doc,
        "upload_id": file_info["upload_id"],
        "message": "File uploaded successfully, processing will begin shortly",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
