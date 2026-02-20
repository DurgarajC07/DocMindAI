# Frontend Integration Guide - New Features

## Overview

The frontend has been enhanced with comprehensive integration of all new backend features including:
- AI Agent Configuration
- Template System
- Prompt Assistant
- Document Processing Progress Tracking
- Advanced RAG Settings

## New Features Integrated

### 1. **Comprehensive API Service Layer** (`lib/api.ts`)

A complete API client covering all backend endpoints:

```typescript
import { 
  authApi, 
  businessApi, 
  agentConfigApi, 
  templateApi, 
  promptAssistantApi,
  promptTemplateApi,
  documentApi,
  chatApi 
} from '@/lib/api'
```

#### Available Services:

**Auth API**
- `authApi.register(data)` - User registration
- `authApi.login(credentials)` - User login
- `authApi.getCurrentUser()` - Get current user

**Business API**
- `businessApi.create(data)` - Create business
- `businessApi.list()` - List all businesses
- `businessApi.get(id)` - Get business details
- `businessApi.update(id, data)` - Update business
- `businessApi.getRAGStats(id)` - Get RAG engine statistics
- `businessApi.clearRAGCache(id)` - Clear RAG cache

**Agent Config API** ✨ NEW
- `agentConfigApi.get(businessId)` - Get agent configuration
- `agentConfigApi.update(businessId, data)` - Update agent config

**Template API** ✨ NEW
- `templateApi.getCategories()` - List template categories
- `templateApi.getWelcomeSuggestions(category)` - Get welcome message suggestions
- `templateApi.getTemplate(category)` - Get specific template
- `templateApi.applyTemplate(businessId, data)` - Apply template to business

**Prompt Assistant API** ✨ NEW
- `promptAssistantApi.analyze(data)` - Analyze prompt quality
- `promptAssistantApi.improve(data)` - Get improved prompt
- `promptAssistantApi.getSamples(category)` - Get sample prompts

**Document API**
- `documentApi.upload(businessId, files, onProgress)` - Upload with progress tracking
- `documentApi.uploadLarge(businessId, file, onProgress)` - Upload large files
- `documentApi.get(businessId, docId)` - Get document status ✨ NEW
- `documentApi.list(businessId)` - List all documents
- `documentApi.delete(businessId, docId)` - Delete document

**Chat API**
- `chatApi.send(businessId, data)` - Send chat message
- `chatApi.sendAdvanced(businessId, data)` - Advanced chat with options ✨ NEW

### 2. **Enhanced Settings Page** (`app/dashboard/settings/page.tsx`)

#### New Agent Configuration Section

Configure AI assistant behavior directly from the UI:

**Fields:**
- **Agent Personality**: Define how the AI behaves (friendly, professional, etc.)
- **Business Category**: Select your industry for better context
- **System Prompt**: Detailed instructions for AI behavior
- **Response Tone**: Professional, friendly, casual, formal, technical, empathetic
- **Hybrid Search**: Enable semantic + keyword search
- **Reranking**: Improve document retrieval relevance
- **Chunk Size**: Control document chunking (100-2000 chars)
- **Chunk Overlap**: Control overlap between chunks (0-500 chars)

**Prompt Assistant Integration:**
- **Analyze Button**: Get quality score and suggestions for your prompt
- **Improve Button**: AI-powered prompt improvement
- **Assistant Panel**: Access prompt samples and best practices

**Template System:**
- Click "Use Template" to open template picker
- Select from pre-configured industry templates:
  - Customer Support
  - Sales
  - Education
  - Healthcare
  - Finance
  - Technology
  - Retail
  - Real Estate
  - Legal

### 3. **Document Processing Progress Tracking** (`app/dashboard/documents/page.tsx`)

#### Real-time Processing Status

**Features:**
- ✅ **Live Status Updates**: Polls backend every 3 seconds for processing status
- 📊 **Processing Banner**: Shows count of documents being processed
- 🔄 **Individual Status**: Each document shows current state:
  - ⏳ "Processing..." with spinner
  - ✓ "Ready" when complete
  - ❌ "Failed" with error message
- 🎉 **Toast Notifications**: Automatic notifications when processing completes/fails

**User Experience:**
```
Upload → "📤 5 file(s) uploaded successfully! Processing..."
  ↓
Processing → "🔄 Chunking document... This may take a few minutes"
  ↓
Complete → "✅ document.pdf processed successfully! (1234 chunks)"
```

**Sequential Processing Banner:**
When multiple files are processing, users see:
```
⏳ Processing 5 documents...
Documents are processed sequentially to ensure reliability.
This may take a few minutes.
```

This informs users about the concurrent upload fix and manages expectations.

### 4. **TypeScript Types** (`lib/types.ts`)

Complete type definitions for all API responses:

```typescript
import type { 
  Business, 
  AgentConfig, 
  Document, 
  ChatResponse,
  PromptAnalysis,
  PromptImprovement,
  Template,
  RAGEngineStats
} from '@/lib/types'
```

## Usage Examples

### Setting Up Agent Configuration

```typescript
// Load agent config
const config = await agentConfigApi.get(businessId)

// Update agent config
await agentConfigApi.update(businessId, {
  agent_personality: 'friendly and helpful',
  business_category: 'customer_support',
  system_prompt: 'You are a customer support agent...',
  response_tone: 'empathetic',
  use_hybrid_search: true,
  use_reranking: true,
  chunk_size: 1000,
  chunk_overlap: 200
})
```

### Using Templates

```typescript
// Get available templates
const categories = await templateApi.getCategories()

// Apply a template
const result = await templateApi.applyTemplate(businessId, {
  category: 'customer_support',
  customize: {
    tone: 'friendly',
    additional_instructions: 'Always ask for clarification'
  }
})
```

### Analyzing Prompts

```typescript
// Analyze prompt quality
const analysis = await promptAssistantApi.analyze({
  prompt: 'You are a helpful assistant',
  context: 'customer_support'
})

console.log(analysis.overall_score) // 0-100
console.log(analysis.suggestions) // Array of improvements

// Get improved prompt
const improvement = await promptAssistantApi.improve({
  prompt: 'You are a helpful assistant',
  context: 'customer_support',
  goals: ['be more specific', 'add personality']
})

console.log(improvement.improved) // Enhanced prompt
console.log(improvement.improvements) // What changed
```

### Tracking Document Processing

```typescript
// Upload with progress
await documentApi.upload(businessId, files, (progress) => {
  console.log(`Upload: ${progress}%`)
})

// Check processing status
const doc = await documentApi.get(businessId, documentId)
if (doc.is_processed) {
  console.log(`Ready! ${doc.chunks_count} chunks`)
} else if (doc.error_message) {
  console.log(`Failed: ${doc.error_message}`)
} else {
  console.log('Still processing...')
}
```

### Using Advanced Chat

```typescript
// Send message with advanced options
const response = await chatApi.sendAdvanced(businessId, {
  message: 'What are your refund policies?',
  session_id: sessionId,
  use_hybrid_search: true,
  use_reranking: true,
  filters: { document_type: 'policy' }
})

console.log(response.answer)
console.log(response.sources) // Array of relevant documents
```

## UI Components Used

### Settings Page
- `Card` - Section containers
- `Input` - Text fields
- `TextArea` - Multi-line text (system prompt)
- `Button` - Actions (save, analyze, improve)
- `Badge` - Status indicators
- `Modal` - Template picker, regenerate key
- `LoadingSpinner` - Loading states

### Documents Page
- `Card` - Document cards
- `Badge` - Status (processing, ready, failed)
- `LoadingSpinner` - Processing indicator
- `Modal` - Upload options
- `Toast` - Notifications

## Environment Configuration

Update `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing the Integration

### 1. Test Agent Configuration

1. Navigate to Settings
2. Scroll to "AI Agent Configuration"
3. Fill in personality, category, system prompt
4. Click "Analyze" to test prompt assistant
5. Click "Use Template" to test template system
6. Toggle RAG settings (hybrid search, reranking)
7. Click "Save Settings"

### 2. Test Document Processing

1. Navigate to Documents
2. Click "Add Content"
3. Upload 3-5 PDFs simultaneously
4. Watch the processing banner appear
5. Each document should show "Processing..." status
6. Wait 1-3 minutes for sequential processing
7. Watch toast notifications as each completes
8. Verify "✓ Ready" badge appears
9. Check chunk count is populated

### 3. Test Prompt Assistant

1. Go to Settings → Agent Configuration
2. Enter a basic system prompt
3. Click "Analyze" - see score and suggestions
4. Click "Improve" - prompt is enhanced
5. Review changes and save

### 4. Test Templates

1. Click "Use Template" in Settings
2. Browse available templates
3. Select "Customer Support"
4. Agent config auto-populates
5. Customize if needed and save

## Error Handling

All API calls automatically handle errors via axios interceptors:

```typescript
// Automatic toast notifications for errors
// 401 errors redirect to login
// Network errors show user-friendly messages
```

Manual error handling (if needed):

```typescript
try {
  await agentConfigApi.update(businessId, data)
} catch (error) {
  // Error already shown to user via toast
  console.error('Update failed:', error)
}
```

## Performance Considerations

1. **Document Polling**: Only polls when documents are processing
2. **Cleanup**: Intervals cleared on component unmount
3. **Debouncing**: Consider adding for rapid updates
4. **Lazy Loading**: Templates loaded on demand

## Known Limitations

1. **Sequential Processing**: Documents process one at a time (by design for reliability)
2. **Polling Frequency**: 3-second intervals (configurable)
3. **File Size Limits**: 50MB per file (backend enforced)
4. **Session Storage**: Business ID in localStorage

## Future Enhancements

Potential additions:
- [ ] Prompt template library UI
- [ ] RAG stats dashboard
- [ ] Conversation analytics
- [ ] Bulk document operations
- [ ] Advanced filtering for documents
- [ ] Export/import agent configurations
- [ ] A/B testing for prompts
- [ ] Real-time chat analytics

## Troubleshooting

### Documents Stuck in Processing

Check:
1. Backend server logs for errors
2. ChromaDB database permissions
3. Network tab for API errors
4. Clear browser cache and reload

### Agent Config Not Saving

Check:
1. All required fields filled
2. Valid chunk size/overlap values
3. Backend logs for validation errors
4. API key still valid

### Templates Not Loading

Check:
1. Backend endpoint `/api/v1/templates/categories`
2. CORS configuration
3. Network connectivity
4. Browser console for errors

## Support

- Backend API documentation: See `backend/main.py`
- Type definitions: See `frontend/lib/types.ts`
- API client: See `frontend/lib/api.ts`
- Concurrent upload fix: See `CONCURRENT_UPLOAD_FIX.md`

---

**Last Updated**: February 20, 2026  
**Frontend Version**: 1.0.0  
**Backend Compatibility**: v1.0.0+
