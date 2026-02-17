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
)
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
    """Process document in background."""
    from backend.database import AsyncSessionLocal
    from backend.rag_engine import RAGEngine
    
    rag_engine = RAGEngine(business_id=business_id)
    
    async with AsyncSessionLocal() as db:
        try:
            # Get document
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc:
                logger.error(f"Document {doc_id} not found")
                return
            
            # Process based on file type
            if file_ext == ".pdf":
                result = await rag_engine.ingest_pdf(file_path)
            elif file_ext in [".txt", ".html"]:
                result = await rag_engine.ingest_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Update document
            doc.is_processed = True
            doc.chunks_count = result["chunks_count"]
            
            # Update business
            business_result = await db.execute(
                select(Business).where(Business.id == business_id)
            )
            business = business_result.scalar_one_or_none()
            if business:
                business.document_count += 1
            
            await db.commit()
            logger.info(f"Document {doc_id} processed successfully: {result['chunks_count']} chunks")
            
        except Exception as e:
            # Update error
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.error_message = str(e)
                await db.commit()
            logger.error(f"Failed to process document {doc_id}: {e}")


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
        logger.info(f"File uploaded: {file.filename} ({file_size} bytes) - processing in background")
    
    await db.commit()
    
    for doc in uploaded_docs:
        await db.refresh(doc)
    
    logger.info(f"Uploaded {len(uploaded_docs)} documents for business {business.id}")
    return {
        "documents": uploaded_docs,
        "message": f"Successfully uploaded {len(uploaded_docs)} documents",
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
    except Exception as e:
        doc.error_message = str(e)
        logger.error(f"Failed to process text content: {e}")
    
    await db.commit()
    await db.refresh(doc)
    
    logger.info(f"Ingested text content for business {business.id}")
    return {
        "documents": [doc],
        "message": "Text content ingested successfully",
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
    
    rag_engine = get_rag_engine(business.id)
    ingested_docs = []
    
    for url in url_data.urls:
        url_str = str(url)
        
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
        except Exception as e:
            doc.error_message = str(e)
            logger.error(f"Failed to process URL {url_str}: {e}")
        
        ingested_docs.append(doc)
    
    await db.commit()
    
    for doc in ingested_docs:
        await db.refresh(doc)
    
    logger.info(f"Ingested {len(ingested_docs)} URLs for business {business.id}")
    return {
        "documents": ingested_docs,
        "message": f"Successfully ingested {len(ingested_docs)} URLs",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
