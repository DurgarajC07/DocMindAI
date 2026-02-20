# Document Processing & Chunking Guide

## Overview
This guide explains how to track document upload and chunking completion in DocMind AI.

## Fixed Issues

### 1. ✅ Route Conflict Fixed
**Problem:** `/api/v1/templates/welcome-suggestions` was being matched by `/api/v1/templates/{category}`

**Solution:** Reordered routes so specific paths come before parameterized ones.

### 2. ✅ Enhanced Logging
**Problem:** No clear logs showing when chunking is complete

**Solution:** Added comprehensive emoji-based logging throughout the document processing pipeline:

```
📤 File uploaded: document.pdf (2048 bytes)
   Document ID: abc123
   Status: Queued for processing
   Check status: GET /api/v1/businesses/{business_id}/documents/abc123

📄 Starting background processing for document abc123
📕 Ingesting PDF document...
✅ Document chunked into 15 pieces
✅ Document abc123 (document.pdf) processing COMPLETE!
   Total chunks: 15
   Status: Ready for queries
```

### 3. ✅ Status Tracking Endpoint
**New Endpoint:** `GET /api/v1/businesses/{business_id}/documents/{document_id}`

This endpoint lets you check if chunking is complete.

## How to Track Document Processing

### Step 1: Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/businesses/{business_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "files=@your-document.pdf"
```

**Response:**
```json
{
  "documents": [
    {
      "id": "doc123",
      "filename": "your-document.pdf",
      "is_processed": false,
      "chunks_count": null,
      "error_message": null
    }
  ],
  "message": "Successfully uploaded 1 document(s). Processing in background..."
}
```

### Step 2: Monitor Server Logs

Watch for these log messages:

```
📤 File uploaded: your-document.pdf (524288 bytes)
   Document ID: doc123
   Status: Queued for processing
   Check status: GET /api/v1/businesses/xyz/documents/doc123

📄 Starting background processing for document doc123
   File: /uploads/xyz/abc_your-document.pdf, Type: .pdf, Business: xyz

📕 Ingesting PDF document...
✅ Document chunked into 42 pieces
✅ Document doc123 (your-document.pdf) processing COMPLETE!
   Total chunks: 42
   Status: Ready for queries
```

### Step 3: Check Document Status

```bash
curl -X GET "http://localhost:8000/api/v1/businesses/{business_id}/documents/{document_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response while processing:**
```json
{
  "id": "doc123",
  "filename": "your-document.pdf",
  "is_processed": false,
  "chunks_count": null,
  "error_message": null,
  "created_at": "2026-02-20T17:30:00Z"
}
```

**Response when complete:**
```json
{
  "id": "doc123",
  "filename": "your-document.pdf",
  "is_processed": true,
  "chunks_count": 42,
  "error_message": null,
  "created_at": "2026-02-20T17:30:00Z"
}
```

**Response if failed:**
```json
{
  "id": "doc123",
  "filename": "your-document.pdf",
  "is_processed": false,
  "chunks_count": null,
  "error_message": "Unsupported file format",
  "created_at": "2026-02-20T17:30:00Z"
}
```

### Step 4: List All Documents

```bash
curl -X GET "http://localhost:8000/api/v1/businesses/{business_id}/documents" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

This returns all documents with their processing status.

## Understanding the Status

| Field | Value | Meaning |
|-------|-------|---------|
| `is_processed` | `false` | Still processing or failed |
| `is_processed` | `true` | Chunking complete, ready for queries |
| `chunks_count` | `null` | Not yet processed |
| `chunks_count` | `15` | Successfully created 15 chunks |
| `error_message` | `null` | No errors |
| `error_message` | `"Error text"` | Processing failed |

## Log Emoji Reference

| Emoji | Meaning |
|-------|---------|
| 📤 | File uploaded |
| 📄 | Processing started |
| 📕 | Processing PDF |
| 📝 | Processing text |
| 🔗 | Processing URL |
| 🌐 | Processing multiple URLs |
| ✅ | Success |
| ❌ | Error |
| ⏳ | In progress |
| 📊 | Summary/Statistics |

## Polling Example (Python)

```python
import requests
import time

def wait_for_processing(business_id, document_id, token, timeout=300):
    """Wait for document processing to complete."""
    url = f"http://localhost:8000/api/v1/businesses/{business_id}/documents/{document_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(url, headers=headers)
        doc = response.json()
        
        if doc["is_processed"]:
            print(f"✅ Processing complete! {doc['chunks_count']} chunks created")
            return doc
        elif doc["error_message"]:
            print(f"❌ Processing failed: {doc['error_message']}")
            return doc
        
        print(f"⏳ Still processing... (elapsed: {int(time.time() - start_time)}s)")
        time.sleep(2)  # Check every 2 seconds
    
    print("⏰ Timeout reached")
    return None

# Usage
doc = wait_for_processing("business123", "doc456", "your_token")
```

## Polling Example (JavaScript)

```javascript
async function waitForProcessing(businessId, documentId, token, timeout = 300000) {
    const url = `http://localhost:8000/api/v1/businesses/${businessId}/documents/${documentId}`;
    const headers = { 'Authorization': `Bearer ${token}` };
    
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
        const response = await fetch(url, { headers });
        const doc = await response.json();
        
        if (doc.is_processed) {
            console.log(`✅ Processing complete! ${doc.chunks_count} chunks created`);
            return doc;
        } else if (doc.error_message) {
            console.log(`❌ Processing failed: ${doc.error_message}`);
            return doc;
        }
        
        console.log(`⏳ Still processing... (elapsed: ${Math.floor((Date.now() - startTime) / 1000)}s)`);
        await new Promise(resolve => setTimeout(resolve, 2000)); // Check every 2 seconds
    }
    
    console.log('⏰ Timeout reached');
    return null;
}

// Usage
const doc = await waitForProcessing('business123', 'doc456', 'your_token');
```

## WebSocket Support (Future Enhancement)

For real-time updates without polling, consider implementing WebSocket notifications:

```python
# Future implementation
@app.websocket("/ws/businesses/{business_id}/documents")
async def document_processing_websocket(websocket: WebSocket, business_id: str):
    await websocket.accept()
    # Send real-time updates as documents are processed
```

## Troubleshooting

### No logs appearing?

1. Check your log level in `backend/config.py`
2. Make sure you're watching the correct terminal
3. Logs appear in the server output where you ran `uvicorn`

### Processing stuck?

1. Check document status endpoint
2. Look for error messages in logs
3. Verify file format is supported (.pdf, .txt, .html)
4. Check file size doesn't exceed plan limits

### Processing failed?

1. Check `error_message` field in document status
2. Review server logs for detailed error traceback
3. Ensure Ollama is running if using LLM features
4. Verify ChromaDB is accessible

## Best Practices

1. **Always check status after upload** - Don't assume processing is instant
2. **Use polling with timeout** - Don't poll forever if something goes wrong
3. **Monitor logs during development** - Logs provide detailed insights
4. **Handle errors gracefully** - Check `error_message` field
5. **Wait for `is_processed: true`** - Before querying the chatbot about the document

## Production Considerations

1. **Implement webhook callbacks** - Instead of polling
2. **Add job queue** - For handling large batch uploads
3. **Use Redis pub/sub** - For real-time status updates
4. **Add progress percentage** - Show % complete for large files
5. **Email notifications** - Notify users when processing completes
