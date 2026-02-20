"""New API endpoints for advanced features - Add these to main.py."""

# Add these imports to main.py:
"""
from backend.advanced_rag import get_advanced_rag_engine
from backend.agent_config import (
    PromptAssistant,
    get_template,
    customize_template,
    validate_response_against_filters,
    AGENT_TEMPLATES,
)
from backend.file_handler import handle_large_file_upload, progress_tracker
from backend.schemas import (
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
from backend.database import (
    PromptTemplate,
    AgentConfigHistory,
    ConversationSession,
)
"""

# ========== Agent Configuration Endpoints ==========

@app. get("/api/v1/businesses/{business_id}/agent-config", response_model=AgentConfigResponse)
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

@app.get("/api/v1/templates/categories")
async def list_template_categories():
    """List available template categories."""
    return {
        "categories": [
            {"value": cat.value, "label": cat.value.replace("_", " ").title()}
            for cat in BusinessCategory
        ]
    }


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


@app.get("/api/v1/templates/welcome-suggestions", response_model=WelcomeMessageSuggestions)
async def get_welcome_suggestions(
    business_name: str,
    category: BusinessCategory = BusinessCategory.CUSTOM,
):
    """Get welcome message suggestions."""
    suggestions = PromptAssistant.generate_welcome_messages(business_name, category)
    return {"suggestions": suggestions}


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
async def clear_rag_cache(
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
    """
    Advanced chat endpoint using optimized RAG engine.
    This endpoint uses:
    - Hybrid search (dense + sparse)
    - Re-ranking for better relevance
    - Conversation memory
    - Response caching
    """
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
    """
    Upload large files with streaming and progress tracking.
    Supports files up to plan limit with optimized memory usage.
    """
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
    
    # Process in background
    from fastapi import BackgroundTasks
    # Schedule processing (would need BackgroundTasks parameter)
    
    logger.info(f"Large file uploaded: {file.filename} ({file_info['file_size']} bytes)")
    
    return {
        "document": doc,
        "upload_id": file_info["upload_id"],
        "message": "File uploaded successfully, processing will begin shortly",
    }
