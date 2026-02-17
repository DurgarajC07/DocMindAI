# Frontend Testing Guide

## Prerequisites
- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend running on `http://localhost:3000`
- ✅ Registered user account

## 1. Document Upload Testing

### Step 1: Navigate to Documents Page
1. Open browser: `http://localhost:3000`
2. Login with your credentials
3. Click on **"Documents"** in the sidebar

### Step 2: Upload PDF Files
1. Click **"Upload Documents"** button
2. Select one or more PDF files (max 50MB each)
3. Click **"Upload"**
4. Wait for processing to complete
5. **Expected Result**: Documents appear in the list with status "Processed"

### Step 3: Upload via URL
1. Click **"Add URL"** button (if available)
2. Enter a website URL (e.g., `https://example.com`)
3. Click **"Ingest"**
4. **Expected Result**: URL appears in documents list

### Test Data Example:
- Upload a small PDF (1-2 pages)
- Check for: filename, file size, chunks count, status

---

## 2. Chat Testing

### Method A: Using Dashboard Chat
1. Go to **Dashboard** page
2. Look for a chat widget or test chat section
3. Type a question related to your uploaded document
   - Example: "What is this document about?"
4. **Expected Result**: Bot responds with relevant answer

### Method B: Using Widget Test Page
1. Create a test HTML file (`test-widget.html`):

```html
<!DOCTYPE html>
<html>
<head>
    <title>Widget Test</title>
</head>
<body>
    <h1>Test DocMind AI Chat Widget</h1>
    
    <!-- Replace YOUR_BUSINESS_ID with actual business ID -->
    <script 
        src="http://localhost:8000/widget.js" 
        data-business-id="YOUR_BUSINESS_ID">
    </script>
</body>
</html>
```

2. Get your Business ID:
   - Go to Settings page
   - Copy the Business ID (UUID format)
3. Replace `YOUR_BUSINESS_ID` in the HTML
4. Open the HTML file in browser
5. Chat widget should appear in bottom-right corner
6. Test conversation:
   - Click widget icon
   - Type: "Hello"
   - Type questions about your documents

### Method C: API Testing (Using curl)
```bash
# Replace BUSINESS_ID with your actual business ID
curl -X POST "http://localhost:8000/api/v1/chat/BUSINESS_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "session_id": "test-session-123"
  }'
```

**Expected Response:**
```json
{
  "answer": "The document discusses...",
  "business_id": "19d08036-9797-4f0f-8279-dfd2b7207025",
  "session_id": "test-session-123",
  "response_time_ms": 2500,
  "sources_count": 3
}
```

---

## 3. Conversations Testing

### View Conversations:
1. Navigate to **Conversations** page
2. **Expected Data**:
   - Session ID
   - User Message
   - Bot Response
   - Timestamp
   - Response Time
   - Feedback status

### Test Multiple Conversations:
1. Send 3-5 different questions via chat
2. Refresh Conversations page
3. **Verify**: All conversations appear in chronological order

### Filter/Search (if available):
- Filter by date range
- Search by keyword
- Filter by session ID

---

## 4. Analytics Testing

### Step 1: Generate Test Data
Before viewing analytics, create some test data:

```bash
# Send multiple chat requests (replace BUSINESS_ID)
for i in {1..10}; do
  curl -X POST "http://localhost:8000/api/v1/chat/BUSINESS_ID" \
    -H "Content-Type: application/json" \
    -d "{\"question\": \"Test question $i\"}"
  sleep 1
done
```

### Step 2: View Analytics Dashboard
1. Navigate to **Analytics** page
2. **Expected Metrics**:
   - **Total Queries**: Shows total number of queries
   - **Queries Today**: Count of today's queries
   - **Unique Sessions Today**: Number of unique users today
   - **Average Response Time**: In milliseconds
   - **Satisfaction Rate**: Based on user feedback (if any)

### Step 3: Test Time Ranges
- Change time range filter (if available)
  - Last 7 days
  - Last 30 days
  - Custom range

### Step 4: View Top Questions
- Should display most frequently asked questions
- Shows count for each question

---

## 5. Settings Testing

### Business Settings:
1. Go to **Settings** page
2. Update business configuration:
   - Business Name
   - Bot Name
   - Welcome Message
   - Theme Color
   - Website URL
3. Click **"Save"**
4. **Verify**: Changes are reflected in chat widget

### Widget Configuration:
1. Copy embed code from Settings
2. Test in external HTML page
3. **Expected**: Widget loads with custom settings

---

## Common Issues & Solutions

### Issue 1: 422 Error on Chat
**Cause**: Missing or invalid request field
**Solution**: Ensure request body has `question` field:
```json
{
  "question": "Your question here",
  "session_id": "optional-session-id"
}
```

### Issue 2: Empty Response
**Cause**: No documents uploaded or processed
**Solution**: 
1. Upload at least one document
2. Wait for processing to complete
3. Try asking a question

### Issue 3: Analytics 500 Error (FIXED)
**Cause**: SQLAlchemy syntax error (now fixed)
**Solution**: Backend code has been updated, restart if needed

### Issue 4: CORS Errors
**Cause**: Frontend running on different port
**Solution**: Check `.env` file has correct CORS_ORIGINS:
```
CORS_ORIGINS=["http://localhost:3000"]
```

---

## Testing Checklist

### Upload Documents ✓
- [ ] Upload PDF successfully
- [ ] View document list
- [ ] See processing status
- [ ] Check chunks count

### Chat Functionality ✓
- [ ] Send message via dashboard
- [ ] Receive relevant answer
- [ ] Test widget embed
- [ ] Multiple conversations work

### Conversations ✓
- [ ] View all conversations
- [ ] See session IDs
- [ ] Response times displayed
- [ ] Timestamps correct

### Analytics ✓
- [ ] Total queries displayed
- [ ] Today's metrics show
- [ ] Average response time calculated
- [ ] Top questions listed

### Settings ✓
- [ ] Update business info
- [ ] Change bot name
- [ ] Modify welcome message
- [ ] Get embed code

---

## Sample Test Workflow

1. **Login** → Navigate to dashboard
2. **Upload Document** → Upload a PDF about your business
3. **Wait for Processing** → Check status becomes "Processed"
4. **Open Chat** → Ask: "What services do you offer?"
5. **Check Response** → Should answer based on document
6. **View Conversations** → See the chat logged
7. **Check Analytics** → Verify query count increased
8. **Repeat 3-5 times** → Generate more data
9. **Review Analytics** → See trends and metrics
10. **Test Widget** → Embed on external page

---

## Quick API Test Commands

```bash
# Set your business ID
export BUSINESS_ID="19d08036-9797-4f0f-8279-dfd2b7207025"

# Test chat
curl -X POST "http://localhost:8000/api/v1/chat/$BUSINESS_ID" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello, how can you help me?"}'

# Get widget config
curl "http://localhost:8000/api/v1/businesses/$BUSINESS_ID/widget-config"

# Get conversations (requires auth token)
curl "http://localhost:8000/api/v1/businesses/$BUSINESS_ID/conversations?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get analytics (requires auth token)
curl "http://localhost:8000/api/v1/businesses/$BUSINESS_ID/analytics?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Notes

- **Session ID**: Used to track conversations from same user
- **Response Time**: Measured in milliseconds (typically 2000-5000ms)
- **Sources Count**: Number of document chunks used to generate answer
- **Was Answered**: True if relevant sources found, False otherwise

Happy Testing! 🚀
