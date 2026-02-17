# 📋 DocMind AI - Commands Cheatsheet

## Quick Commands

```bash
# Setup (first time only)
./setup.sh

# Run application
./run.sh

# Test installation
./test_setup.py

# Check health
curl http://localhost:8000/health
```

## Installation Commands

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Install Redis
sudo apt-get install -y redis-server

# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install
```

## Ollama Commands

```bash
# Start Ollama
sudo systemctl start ollama

# Check Ollama status
sudo systemctl status ollama

# List models
ollama list

# Pull Mistral model
ollama pull mistral:7b-instruct-v0.3-q4_K_M

# Test Ollama
ollama run mistral "Hello, how are you?"

# Remove model
ollama rm mistral:7b-instruct-v0.3-q4_K_M
```

## Redis Commands

```bash
# Start Redis
sudo systemctl start redis

# Stop Redis
sudo systemctl stop redis

# Check Redis status
redis-cli ping

# View Redis data
redis-cli
> KEYS *
> GET key_name
> FLUSHALL  # Clear all data
```

## Database Commands

```bash
# Initialize database
uv run python -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"

# View database (SQLite)
sqlite3 docmind.db

# List tables
sqlite3 docmind.db ".tables"

# Count businesses
sqlite3 docmind.db "SELECT COUNT(*) FROM businesses;"

# Count documents
sqlite3 docmind.db "SELECT COUNT(*) FROM documents;"

# Count conversations
sqlite3 docmind.db "SELECT COUNT(*) FROM conversations;"

# View recent conversations
sqlite3 docmind.db "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;"

# Reset database (DANGER)
rm docmind.db
uv run python -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"
```

## Backend Commands

```bash
# Run backend (development)
uv run uvicorn backend.main:app --reload

# Run backend (production)
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4

# Run on different port
uv run uvicorn backend.main:app --port 8001

# Check backend logs
tail -f logs/docmind.log

# Python REPL with project context
uv run python
>>> from backend.database import *
>>> from backend.rag_engine import *
```

## Frontend Commands

```bash
# Run development server
cd frontend && npm run dev

# Build for production
cd frontend && npm run build

# Start production server
cd frontend && npm start

# Lint code
cd frontend && npm run lint

# Install new package
cd frontend && npm install package-name
```

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild images
docker-compose build

# Pull Mistral in Ollama container
docker exec -it docmind-ollama ollama pull mistral:7b-instruct-v0.3-q4_K_M

# Access backend container
docker exec -it docmind-backend bash

# Access database container
docker exec -it docmind-postgres psql -U docmind
```

## API Testing Commands

### Authentication

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Save token
TOKEN="your-token-here"

# Get user info
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Business Management

```bash
# Create business
curl -X POST http://localhost:8000/api/v1/businesses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Business",
    "website": "https://example.com",
    "description": "Test business"
  }'

# List businesses
curl http://localhost:8000/api/v1/businesses \
  -H "Authorization: Bearer $TOKEN"

# Get specific business
BUSINESS_ID="abc123"
curl http://localhost:8000/api/v1/businesses/$BUSINESS_ID \
  -H "Authorization: Bearer $TOKEN"

# Update business
curl -X PATCH http://localhost:8000/api/v1/businesses/$BUSINESS_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bot_name": "ChatBot Pro",
    "theme_color": "#FF6B6B"
  }'

# Delete business
curl -X DELETE http://localhost:8000/api/v1/businesses/$BUSINESS_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Document Management

```bash
# Upload PDF
curl -X POST http://localhost:8000/api/v1/businesses/$BUSINESS_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@/path/to/document.pdf"

# Upload multiple files
curl -X POST http://localhost:8000/api/v1/businesses/$BUSINESS_ID/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@file1.pdf" \
  -F "files=@file2.txt"

# Ingest URLs
curl -X POST http://localhost:8000/api/v1/businesses/$BUSINESS_ID/documents/urls \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com/about",
      "https://example.com/faq"
    ]
  }'

# List documents
curl http://localhost:8000/api/v1/businesses/$BUSINESS_ID/documents \
  -H "Authorization: Bearer $TOKEN"

# Delete document
DOC_ID="doc-123"
curl -X DELETE http://localhost:8000/api/v1/businesses/$BUSINESS_ID/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Chat

```bash
# Send message (no auth required)
curl -X POST http://localhost:8000/api/v1/chat/$BUSINESS_ID \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are your business hours?",
    "session_id": "optional-session-id"
  }'

# Get widget config
curl http://localhost:8000/api/v1/businesses/$BUSINESS_ID/widget-config
```

### Analytics

```bash
# Get analytics
curl http://localhost:8000/api/v1/businesses/$BUSINESS_ID/analytics \
  -H "Authorization: Bearer $TOKEN"

# Get conversations
curl http://localhost:8000/api/v1/businesses/$BUSINESS_ID/conversations \
  -H "Authorization: Bearer $TOKEN"

# Get specific number of conversations
curl "http://localhost:8000/api/v1/businesses/$BUSINESS_ID/conversations?limit=100" \
  -H "Authorization: Bearer $TOKEN"

# Submit feedback
CONV_ID="conv-123"
curl -X POST http://localhost:8000/api/v1/conversations/$CONV_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv-123",
    "feedback": 1
  }'
```

### Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Pretty print JSON
curl http://localhost:8000/health | jq

# Check specific endpoint response time
time curl http://localhost:8000/health
```

## Python Commands

```bash
# Run Python shell with project
uv run python

# Test RAG engine
uv run python -c "
from backend.rag_engine import RAGEngine
engine = RAGEngine('test')
print(engine.get_collection_stats())
"

# Test database
uv run python -c "
import asyncio
from backend.database import init_db
asyncio.run(init_db())
print('Database initialized')
"

# Test embeddings
uv run python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embedding = model.encode('test')
print(f'Embedding shape: {embedding.shape}')
"
```

## File Operations

```bash
# View logs
tail -f logs/docmind.log

# Follow logs with grep
tail -f logs/docmind.log | grep ERROR

# Count errors in logs
grep ERROR logs/docmind.log | wc -l

# View ChromaDB collections
ls -la data/chroma/

# View uploaded files
ls -la uploads/

# Check disk usage
du -sh data/ uploads/ logs/

# Clean up old files
find uploads/ -mtime +30 -delete  # Delete files older than 30 days
```

## System Monitoring

```bash
# Check GPU usage (if NVIDIA)
nvidia-smi

# Watch GPU in real-time
watch -n 1 nvidia-smi

# Check RAM usage
free -h

# Check CPU usage
top
htop

# Check disk space
df -h

# Check network
netstat -tulpn | grep :8000

# Check processes
ps aux | grep uvicorn
ps aux | grep ollama
```

## Backup & Restore

```bash
# Backup database
cp docmind.db backups/docmind-$(date +%Y%m%d).db

# Backup ChromaDB
tar -czf backups/chroma-$(date +%Y%m%d).tar.gz data/chroma/

# Backup uploads
tar -czf backups/uploads-$(date +%Y%m%d).tar.gz uploads/

# Restore database
cp backups/docmind-20260215.db docmind.db

# Restore ChromaDB
tar -xzf backups/chroma-20260215.tar.gz -C data/
```

## Development Commands

```bash
# Format code with Black
uv run black backend/

# Lint with Ruff
uv run ruff check backend/

# Type check with MyPy
uv run mypy backend/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=backend

# Generate coverage report
uv run pytest --cov=backend --cov-report=html
```

## Git Commands

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - DocMind AI v1.0"

# Add remote
git remote add origin https://github.com/yourusername/docmind-ai.git

# Push
git push -u origin main

# Create new branch
git checkout -b feature/new-feature

# View status
git status

# View logs
git log --oneline
```

## Troubleshooting Commands

```bash
# Check all services
systemctl status ollama
systemctl status redis
ps aux | grep uvicorn

# Kill stuck processes
pkill -f uvicorn
pkill -f ollama

# Clear Redis cache
redis-cli FLUSHALL

# Reset ChromaDB
rm -rf data/chroma/*
mkdir -p data/chroma

# Check ports in use
sudo lsof -i :8000
sudo lsof -i :11434
sudo lsof -i :6379

# Test Ollama connection
curl http://localhost:11434/api/tags

# Test Redis connection
redis-cli ping
```

## Performance Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test API endpoint
ab -n 100 -c 10 http://localhost:8000/health

# Load test chat endpoint
ab -n 50 -c 5 -p chat.json -T application/json \
  http://localhost:8000/api/v1/chat/$BUSINESS_ID

# Create chat.json
echo '{"question":"What is your refund policy?"}' > chat.json
```

## Production Deployment

```bash
# Set production environment
export ENVIRONMENT=production
export DEBUG=false

# Run with multiple workers
uv run uvicorn backend.main:app --workers 4 --host 0.0.0.0 --port 8000

# Run with Gunicorn (alternative)
uv run gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Setup systemd service
sudo cp docmind.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable docmind
sudo systemctl start docmind

# View service logs
sudo journalctl -u docmind -f

# Setup Nginx reverse proxy
sudo apt-get install nginx
sudo cp docmind-nginx.conf /etc/nginx/sites-available/docmind
sudo ln -s /etc/nginx/sites-available/docmind /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Setup SSL with Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Useful Aliases

Add to `~/.bashrc`:

```bash
alias docmind-start='cd ~/Desktop/Projects/DocMindAI && ./run.sh'
alias docmind-test='cd ~/Desktop/Projects/DocMindAI && ./test_setup.py'
alias docmind-logs='tail -f ~/Desktop/Projects/DocMindAI/logs/docmind.log'
alias docmind-db='sqlite3 ~/Desktop/Projects/DocMindAI/docmind.db'
```

Then run: `source ~/.bashrc`

---

**💡 Tip**: Save this file and use `grep` to quickly find commands!

```bash
grep -i "redis" CHEATSHEET.md
grep -i "backup" CHEATSHEET.md
```
