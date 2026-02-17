# 🚀 DocMind AI - Quick Start Guide

## Installation (5 minutes)

### System Requirements
- Ubuntu/Fedora/Debian Linux
- 16GB RAM minimum
- NVIDIA GPU with 6GB+ VRAM (optional but recommended)
- 20GB free disk space

### Install Dependencies

```bash
# 1. Install Ollama (LLM runtime)
curl -fsSL https://ollama.com/install.sh | sh

# 2. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 3. Install Redis
sudo apt-get update && sudo apt-get install -y redis-server
sudo systemctl start redis
sudo systemctl enable redis

# 4. Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Setup Project

```bash
cd /home/coller/Desktop/Projects/DocMindAI

# Run automated setup
./setup.sh

# This will:
# - Install Python dependencies with uv
# - Download Mistral model via Ollama
# - Initialize database
# - Install frontend dependencies
# - Generate secure secret keys
```

## Running the Application

### Option 1: One-Command Start (Recommended)

```bash
./run.sh
```

This starts both backend and frontend automatically.

### Option 2: Manual Start

```bash
# Terminal 1: Backend
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (optional)
cd frontend && npm run dev
```

### Access Points

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000

## First Steps

### 1. Create an Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

Save the `access_token` from the response.

### 3. Create a Business

```bash
TOKEN="your-access-token-here"

curl -X POST http://localhost:8000/api/v1/businesses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Test Business",
    "website": "https://example.com",
    "description": "Test chatbot"
  }'
```

Save the `business_id` and `api_key` from the response.

### 4. Upload a Test Document

Create a test PDF or use any existing PDF:

```bash
BUSINESS_ID="your-business-id"

curl -X POST http://localhost:8000/api/v1/businesses/$BUSINESS_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/your/document.pdf"
```

### 5. Test the Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/$BUSINESS_ID \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?"
  }'
```

### 6. Embed Widget on Website

Create `test.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>DocMind AI Test</title>
</head>
<body>
    <h1>My Website with AI Chatbot</h1>
    <p>Try the chatbot in the bottom right corner!</p>
    
    <!-- Embed DocMind AI Widget -->
    <script 
        src="http://localhost:8000/widget.js" 
        data-business-id="YOUR_BUSINESS_ID_HERE">
    </script>
</body>
</html>
```

Open `test.html` in your browser.

## Testing the Installation

Run the test script to verify everything is working:

```bash
./test_setup.py
```

This will check:
- ✓ Python packages
- ✓ Database connection
- ✓ Configuration
- ✓ Ollama LLM
- ✓ Redis cache
- ✓ Embedding model
- ✓ RAG engine

## Common Issues & Solutions

### Issue: Ollama not running

```bash
sudo systemctl start ollama
ollama list  # Check models
ollama pull mistral:7b-instruct-v0.3-q4_K_M  # Download model
```

### Issue: Redis connection error

```bash
sudo systemctl start redis
redis-cli ping  # Should return PONG
```

### Issue: GPU not detected

Edit `.env` and change:
```bash
EMBEDDING_DEVICE=cpu
```

### Issue: Port already in use

Change ports in `.env`:
```bash
# Frontend: Edit frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001

# Backend: Run with different port
uv run uvicorn backend.main:app --port 8001
```

### Issue: Database locked

```bash
rm docmind.db
uv run python -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"
```

## API Quick Reference

### Authentication
```bash
# Register
POST /api/v1/auth/register

# Login
POST /api/v1/auth/login

# Get user info
GET /api/v1/auth/me
```

### Business Management
```bash
# Create business
POST /api/v1/businesses

# List businesses
GET /api/v1/businesses

# Update business
PATCH /api/v1/businesses/{id}
```

### Document Management
```bash
# Upload documents
POST /api/v1/businesses/{id}/documents

# Upload URLs
POST /api/v1/businesses/{id}/documents/urls

# List documents
GET /api/v1/businesses/{id}/documents
```

### Chat
```bash
# Send message (no auth required)
POST /api/v1/chat/{business_id}

# Get widget config
GET /api/v1/businesses/{id}/widget-config
```

### Analytics
```bash
# Get analytics
GET /api/v1/businesses/{id}/analytics

# Get conversations
GET /api/v1/businesses/{id}/conversations
```

## Production Deployment

### Using Docker

```bash
# Start all services
docker-compose up -d

# Pull Mistral model
docker exec -it docmind-ollama ollama pull mistral:7b-instruct-v0.3-q4_K_M

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Systemd Services

Create `/etc/systemd/system/docmind.service`:

```ini
[Unit]
Description=DocMind AI Backend
After=network.target redis.service ollama.service

[Service]
Type=simple
User=coller
WorkingDirectory=/home/coller/Desktop/Projects/DocMindAI
Environment="PATH=/home/coller/.cargo/bin:/usr/bin"
ExecStart=/home/coller/.cargo/bin/uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable docmind
sudo systemctl start docmind
sudo systemctl status docmind
```

## Environment Variables

Key settings in `.env`:

```bash
# App
APP_NAME=DocMind AI
DEBUG=false  # Set to false in production
SECRET_KEY=<generated-secure-key>

# Database
DATABASE_URL=sqlite+aiosqlite:///./docmind.db
# Or PostgreSQL: postgresql+asyncpg://user:pass@localhost/docmind

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct-v0.3-q4_K_M

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cuda  # or cpu

# Security
JWT_SECRET_KEY=<generated-secure-key>
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

## Performance Tuning

### For Low-End Hardware (8GB RAM)

```bash
# Use smaller model
OLLAMA_MODEL=mistral:7b-instruct-q2_K

# Use CPU for embeddings
EMBEDDING_DEVICE=cpu

# Reduce chunk size in backend/rag_engine.py
chunk_size=300  # Instead of 500
```

### For High-End Hardware (32GB RAM, RTX 4090)

```bash
# Use larger model
OLLAMA_MODEL=llama3.1:70b

# Use GPU for everything
EMBEDDING_DEVICE=cuda

# Increase chunk size
chunk_size=1000
```

## Monitoring

### Check Logs

```bash
# Backend logs
tail -f logs/docmind.log

# System logs
journalctl -u docmind -f
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Database Status

```bash
sqlite3 docmind.db "SELECT COUNT(*) FROM businesses;"
sqlite3 docmind.db "SELECT COUNT(*) FROM documents;"
sqlite3 docmind.db "SELECT COUNT(*) FROM conversations;"
```

## Backup

```bash
# Backup database
cp docmind.db docmind.db.backup

# Backup vector store
tar -czf chroma-backup.tar.gz data/chroma/

# Backup uploads
tar -czf uploads-backup.tar.gz uploads/
```

## Getting Help

- 📖 Read the complete [README.md](README.md)
- 🔧 Check [plan.txt](plan.txt) for architecture details
- 📝 View API docs at http://localhost:8000/docs
- 🐛 Run `./test_setup.py` to diagnose issues

---

**Ready to build and ship your AI chatbot SaaS! 🚀**
