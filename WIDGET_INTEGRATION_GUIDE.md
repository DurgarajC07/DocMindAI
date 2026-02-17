# 🚀 DocMind AI Widget Integration Guide

## 📦 Quick Start

The DocMind AI widget can be embedded in **2 ways**:

### Method 1: Simple Auto-Init (Recommended) ✨

Add this single line before your closing `</body>` tag:

```html
<script 
    src="http://localhost:8000/widget.js" 
    data-business-id="19d08036-9797-4f0f-8279-dfd2b7207025"
    data-api-base="http://localhost:8000">
</script>
```

**That's it!** The widget will automatically initialize when the page loads.

### Method 2: Manual Initialization 🔧

For more control (e.g., in SPAs or conditional loading):

```html
<!-- Load script first -->
<script src="http://localhost:8000/widget.js"></script>

<!-- Then initialize manually -->
<script>
  document.addEventListener("DOMContentLoaded", function() {
    DocMindWidget.init({
      businessId: '19d08036-9797-4f0f-8279-dfd2b7207025',
      apiUrl: 'http://localhost:8000'
    });
  });
</script>
```

---

## 🔑 Configuration

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `businessId` | Your unique business ID | `19d08036-9797-4f0f-8279-dfd2b7207025` |
| `apiUrl` | Backend API URL | `http://localhost:8000` |

### Optional Attributes (Auto-Init)

- `data-business-id`: Your business ID (required)
- `data-api-base`: API base URL (optional, defaults to localhost:8000)

---

## 📝 Test Files Provided

We've created test files for you:

### 1. **test-widget.html** - Simple Auto-Init
- Basic, recommended approach
- Widget loads automatically
- Open in browser: `file:///path/to/test-widget.html`

### 2. **test-widget-manual.html** - Manual Init
- Shows manual initialization
- Good for SPAs or dynamic loading
- Open in browser: `file:///path/to/test-widget-manual.html`

---

## 🎨 Widget Features

✅ **Automatic Configuration Loading**
- Bot name, colors, and messages from your business settings

✅ **Session Persistence**
- Conversations continue across page reloads
- Uses localStorage for session tracking

✅ **Mobile Responsive**
- Works on all screen sizes
- Touch-friendly interface

✅ **Real-time Chat**
- Instant responses from your AI
- Loading indicators during processing

✅ **Error Handling**
- Graceful fallbacks for network issues
- User-friendly error messages

---

## 🧪 Testing Your Widget

### Step 1: Verify Backend is Running
Open: http://localhost:8000/docs

Should show FastAPI documentation.

### Step 2: Test Widget Endpoint
Open: http://localhost:8000/widget.js

Should download/show JavaScript code.

### Step 3: Check Business Configuration
```bash
curl http://localhost:8000/api/v1/businesses/19d08036-9797-4f0f-8279-dfd2b7207025/widget-config
```

Should return JSON with bot_name, theme_color, etc.

### Step 4: Test Chat API Directly
```bash
curl -X POST "http://localhost:8000/api/v1/chat/19d08036-9797-4f0f-8279-dfd2b7207025" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello, how can you help me?"}'
```

Should return a JSON response with `answer`, `session_id`, etc.

### Step 5: Open Test File
1. Open `test-widget.html` in your browser
2. Look for chat bubble in bottom-right corner
3. Click to open chat window
4. Type a message and send

---

## 🐛 Troubleshooting

### Widget Not Appearing?

**Check Console (F12)**
Look for error messages:

- ❌ `Failed to load widget.js` → Backend not running or wrong URL
- ❌ `Missing data-business-id` → Add required attribute
- ❌ `Failed to load config` → Check business ID is correct

**Verify Business ID**
```javascript
// In browser console
localStorage.getItem('docmind_session_19d08036-9797-4f0f-8279-dfd2b7207025')
```

### Widget Loads But No Response?

**1. Check Documents**
- Go to dashboard → Documents
- Verify at least one document is uploaded and processed
- Status should show "Processed" not "Failed"

**2. Check Network Tab**
- Open Developer Tools (F12) → Network
- Send a message
- Look for POST request to `/api/v1/chat/...`
- Check response status and body

**3. Verify Backend Logs**
Look for errors in terminal where backend is running.

### CORS Errors?

If you see CORS errors in console:

**Solution 1: Update .env**
```bash
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","file://"]
```

**Solution 2: Serve via HTTP**
Don't open HTML files directly (`file://`), instead:

```bash
# Simple HTTP server
cd /path/to/your/files
python3 -m http.server 8080

# Then open: http://localhost:8080/test-widget.html
```

### "Question Field Required" Error?

This is already fixed in the latest code. If you still see it:

**Check Widget Code**
The widget should send:
```javascript
{
  "question": "user message here",
  "session_id": "session-uuid"
}
```

NOT:
```javascript
{
  "message": "user message here",  // ❌ Wrong
  ...
}
```

---

## 🌐 Production Deployment

### 1. Update URLs

Replace `localhost` with your domain:

```html
<script 
    src="https://your-domain.com/widget.js" 
    data-business-id="YOUR_BUSINESS_ID"
    data-api-base="https://your-domain.com">
</script>
```

### 2. Update CORS Settings

In your `.env` file:
```bash
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]
```

### 3. Use HTTPS

Always use HTTPS in production for security.

### 4. CDN (Optional)

For better performance, serve `widget.js` via CDN:
- CloudFlare
- AWS CloudFront
- Fastly

---

## 🎯 Advanced Usage

### Customization via Code

```javascript
DocMindWidget.init({
  businessId: 'YOUR_BUSINESS_ID',
  apiUrl: 'https://your-api.com',
  // Position
  position: 'bottom-right', // or 'bottom-left'
  // Custom colors (overrides server config)
  theme_color: '#2563eb',
  // Custom messages
  welcome_message: 'Hi! How can I help?',
  bot_name: 'Support Bot'
});
```

### Multiple Widgets on Same Page

```javascript
// Widget 1 - Sales Bot
DocMindWidget.init({
  businessId: 'sales-bot-id',
  position: 'bottom-right'
});

// Widget 2 - Support Bot  
DocMindWidget.init({
  businessId: 'support-bot-id',
  position: 'bottom-left'
});
```

---

## 📊 API Reference

### Widget Endpoint
```
GET /widget.js
```
Returns the widget JavaScript code.

### Chat Endpoint  
```
POST /api/v1/chat/{business_id}
```

**Request Body:**
```json
{
  "question": "User's question",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "AI response",
  "business_id": "uuid",
  "session_id": "uuid",
  "response_time_ms": 2500,
  "sources_count": 3
}
```

### Widget Config Endpoint
```
GET /api/v1/businesses/{business_id}/widget-config
```

**Response:**
```json
{
  "bot_name": "AI Assistant",
  "welcome_message": "Hi!",
  "theme_color": "#2563eb"
}
```

---

## 🔐 Security

### API Key Usage

For authenticated requests (not needed for public chat):

```javascript
fetch(`${apiUrl}/api/v1/businesses/${businessId}/documents`, {
  headers: {
    'Authorization': `Bearer ${apiKey}`
  }
})
```

### Rate Limiting

The backend automatically enforces rate limits based on your plan:
- Free: 50 queries/month
- Starter: 1,000 queries/month
- Pro: 10,000 queries/month
- Enterprise: Unlimited

---

## 📞 Support

### Check Logs
```bash
# Backend logs
tail -f logs/docmind.log

# Or in terminal where backend is running
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8000/

# API docs
open http://localhost:8000/docs
```

### Common Issues
1. **Widget not loading**: Check backend is running
2. **No responses**: Upload and process documents first
3. **CORS errors**: Update CORS_ORIGINS in .env
4. **422 errors**: Fixed in latest code, restart backend

---

## ✅ Checklist

Before going live, verify:

- [ ] Backend is running and accessible
- [ ] At least one document uploaded and processed
- [ ] Widget appears on test page
- [ ] Chat messages send and receive responses
- [ ] Conversations logged in dashboard
- [ ] Analytics updating correctly
- [ ] CORS configured for your domain
- [ ] HTTPS enabled in production
- [ ] API key kept secret
- [ ] Rate limits appropriate for your plan

---

**Ready to go! 🚀**

Need help? Check:
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Test Files: `test-widget.html` and `test-widget-manual.html`
