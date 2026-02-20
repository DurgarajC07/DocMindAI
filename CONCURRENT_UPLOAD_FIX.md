# Concurrent Upload Fix - ChromaDB SQLite Lock Issue

## Problem Overview

### Issue
When uploading **multiple PDF files simultaneously**, all documents failed with:
```
chromadb.errors.InternalError: Query error: Database error: 
error returned from database: (code: 1032) attempt to write a readonly database
```

### Root Cause
1. **SQLite Concurrency Limitation**: ChromaDB uses SQLite internally for metadata storage
2. **No Write Synchronization**: Multiple background tasks tried to write to ChromaDB simultaneously
3. **SQLite Locking Behavior**: SQLite locks the entire database file during write operations
4. **Race Condition**: When 5+ files upload at once, tasks compete for database lock causing "readonly" errors

### Technical Details
```python
# Before Fix: Multiple tasks write concurrently
Task 1: Processing durgaraj.pdf        -> Writes to DB ← Lock acquired
Task 2: Processing HCI Alan Dix.pdf    -> Tries to write  ❌ DATABASE LOCKED
Task 3: Processing NLP jurafsky.pdf    -> Tries to write  ❌ DATABASE LOCKED
Task 4: Processing Machine Learning    -> Tries to write  ❌ DATABASE LOCKED
Task 5: Processing Data Science.pdf    -> Tries to write  ❌ DATABASE LOCKED
```

## Solution Implemented

### 1. **AsyncIO Lock Mechanism**
Added a **class-level asyncio.Lock** that all RAG engine instances share:

```python
class RAGEngine:
    # Shared lock across ALL instances
    _vector_store_lock = asyncio.Lock()
```

### 2. **Serialized Vector Store Writes**
Wrapped all vector store write operations with lock:

```python
async with RAGEngine._vector_store_lock:
    logger.info(f"🔒 Acquired vector store lock for {source}")
    self.vector_store.add_documents(valid_chunks)
    logger.info(f"✅ Added {len(valid_chunks)} chunks")
```

### 3. **Applied to Both Engines**
- `backend/rag_engine.py` - Basic RAG engine
- `backend/advanced_rag.py` - Advanced RAG with hybrid search

## How It Works Now

```python
# After Fix: Serialized writes with lock
Task 1: 🔒 Lock acquired → Write to DB → ✅ Release lock
Task 2:    Wait for lock → 🔒 Acquired → Write → ✅ Release
Task 3:    Wait for lock → 🔒 Acquired → Write → ✅ Release
Task 4:    Wait for lock → 🔒 Acquired → Write → ✅ Release
Task 5:    Wait for lock → 🔒 Acquired → Write → ✅ Release
```

### Logging Output Example
```
2026-02-20 18:41:14 | INFO | Sanitized 5126 chunks down to 5126 valid chunks
2026-02-20 18:41:14 | INFO | 🔒 Acquired vector store lock for uploads/.../HCI.pdf
2026-02-20 18:41:18 | INFO | ✅ Added 5126 chunks from uploads/.../HCI.pdf to vector store
2026-02-20 18:41:18 | INFO | 🔒 Acquired vector store lock for uploads/.../NLP.pdf
2026-02-20 18:41:22 | INFO | ✅ Added 4905 chunks from uploads/.../NLP.pdf to vector store
```

## Performance Characteristics

### Before Fix
- ❌ Concurrent writes failed
- ❌ All background tasks crashed
- ❌ No documents processed successfully
- ❌ Database corruption risk

### After Fix
- ✅ Sequential processing (one at a time)
- ✅ All uploads eventually succeed
- ✅ No database errors
- ✅ Safe and reliable

### Performance Trade-offs
- **Slower overall time** when uploading many files (no parallelization)
- **More predictable** processing time
- **No race conditions** or database errors
- **Better memory usage** (no concurrent embedding operations)

## Testing Multiple Uploads

### Upload 5 PDFs Simultaneously
```bash
curl -X POST "http://localhost:8000/api/v1/businesses/{BUSINESS_ID}/documents" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@doc3.pdf" \
  -F "files=@doc4.pdf" \
  -F "files=@doc5.pdf"
```

### Watch Processing in Real-time
```bash
# Follow server logs
tail -f logs/app.log | grep "vector store lock"
```

### Check Processing Status
```bash
# Poll document status
curl "http://localhost:8000/api/v1/businesses/{BUSINESS_ID}/documents/{DOC_ID}"
```

## Why This Approach?

### Alternative Solutions Considered

#### 1. **Queue-based Processing** ❌
```python
# Pros: Decoupled, scalable
# Cons: Requires message broker (Redis, RabbitMQ), complexity
```

#### 2. **Process Pool** ❌
```python
# Pros: True parallelism
# Cons: High memory usage, embedding model loaded multiple times
```

#### 3. **Different ChromaDB Backend** ❌
```python
# Pros: Better concurrency (PostgreSQL, DuckDB)
# Cons: Complex deployment, external dependencies
```

#### 4. **AsyncIO Lock** ✅ **CHOSEN**
```python
# Pros: Simple, no dependencies, immediate fix
# Cons: Sequential processing (acceptable for now)
```

## Production Considerations

### For Small-Scale Deployments (< 100 docs/hour)
- ✅ Current solution is **adequate**
- Simple, reliable, no extra infrastructure

### For High-Volume Deployments (> 1000 docs/hour)
Consider upgrading to:

1. **Celery + Redis** for distributed task queue
   ```python
   @celery.app.task
   async def process_document_async(doc_id: str):
       # Process in separate worker
   ```

2. **ChromaDB Client-Server Mode**
   ```python
   # Better concurrent write handling
   chroma_client = chromadb.HttpClient(host="chroma-server")
   ```

3. **Batch Processing**
   ```python
   # Collect uploads, process every N minutes
   await process_batch(pending_documents)
   ```

## Code Changes Summary

### Files Modified
1. **backend/rag_engine.py**
   - Added `import asyncio`
   - Added class-level `_vector_store_lock = asyncio.Lock()`
   - Wrapped `vector_store.add_documents()` with lock

2. **backend/advanced_rag.py**
   - Added class-level `_vector_store_lock = asyncio.Lock()`
   - Wrapped batch writes with lock
   - Added progress logging for batches

3. **data/chroma/** permissions
   - Ensured `755` permissions on chroma directory

## Verification Steps

### 1. Upload Multiple Files
Upload 5-10 PDFs simultaneously through the API

### 2. Monitor Logs for Lock Acquisition
Should see:
```
🔒 Acquired vector store lock for file1.pdf
✅ Added N chunks...
🔒 Acquired vector store lock for file2.pdf
✅ Added N chunks...
```

### 3. Check All Documents Processed
Query the database:
```sql
SELECT filename, is_processed, chunks_count, error_message 
FROM documents 
WHERE business_id = 'YOUR_BUSINESS_ID';
```

### 4. Verify No Errors
All documents should have:
- `is_processed = 1`
- `chunks_count > 0`
- `error_message = NULL`

## Future Optimizations

### Phase 1: Batching (Easy)
```python
# Group uploads by business, process together
await process_documents_batch(business_id, document_ids)
```

### Phase 2: Queue System (Medium)
```python
# Add Celery for distributed processing
celery = Celery('docmind', broker='redis://localhost')
```

### Phase 3: ChromaDB Server (Hard)
```python
# Deploy dedicated ChromaDB server
docker run -d -p 8001:8000 chromadb/chroma
```

## Troubleshooting

### Still Getting "readonly database" Errors?

1. **Check Permissions**
   ```bash
   ls -la data/chroma/
   chmod -R 755 data/chroma/
   ```

2. **Restart Server**
   ```bash
   # Ensure new code is loaded
   uvicorn backend.main:app --reload
   ```

3. **Check for Hung Processes**
   ```bash
   # Kill any processes holding database locks
   ps aux | grep python
   ```

4. **Delete and Recreate ChromaDB**
   ```bash
   # CAUTION: Loses all vector embeddings
   rm -rf data/chroma/*
   # Will be recreated on next upload
   ```

## Monitoring Recommendations

### Add These Metrics
1. **Lock wait time** - How long tasks wait for lock
2. **Concurrent upload count** - Track simultaneous uploads
3. **Processing queue depth** - Number of pending documents
4. **Average processing time** - Per-document metrics

### Example Prometheus Metrics
```python
from prometheus_client import Histogram, Counter

vector_store_lock_duration = Histogram(
    'vector_store_lock_duration_seconds',
    'Time spent waiting for vector store lock'
)

concurrent_uploads = Counter(
    'concurrent_document_uploads_total',
    'Number of concurrent document uploads'
)
```

## Summary

✅ **Problem**: Concurrent uploads caused SQLite lock errors  
✅ **Solution**: Added asyncio.Lock to serialize vector store writes  
✅ **Result**: All uploads now succeed reliably  
✅ **Trade-off**: Sequential processing (slower but reliable)  
✅ **Status**: Production-ready for small-medium workloads  

---

**Last Updated**: February 20, 2026  
**Author**: GitHub Copilot  
**Status**: ✅ Implemented and Tested
