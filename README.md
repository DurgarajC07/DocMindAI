# 🚀 DocMind AI - Custom AI Chatbot Builder for Businesses

![Python 3.14](https://img.shields.io/badge/python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)
![Next.js 15](https://img.shields.io/badge/Next.js-15-black)
![License](https://img.shields.io/badge/license-MIT-blue)

A production-ready, self-hosted AI chatbot platform that allows businesses to train custom chatbots on their own documents, PDFs, and website content using RAG (Retrieval-Augmented Generation).

## ✨ Features

- 🤖 **Custom AI Training** - Upload PDFs, text files, or website URLs to train your chatbot
- 💬 **Embeddable Widget** - One-line integration for any website
- 📊 **Analytics Dashboard** - Track queries, response times, and customer satisfaction
- 🔐 **Multi-tenancy** - Secure isolation for multiple businesses
- 🚀 **Production Ready** - Built with FastAPI, ChromaDB, and Next.js
- 💰 **Cost Effective** - Uses open-source models (Mistral/LLaMA) via Ollama
- 🌍 **Multilingual** - Supports Hindi, English, and more
- ⚡ **Fast** - Optimized RAG pipeline with vector search
- 🎨 **Customizable** - Brand colors, bot names, welcome messages

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Next.js   │────────▶│   FastAPI    │────────▶│   Ollama    │
│  Dashboard  │         │   Backend    │         │  (Mistral)  │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              ┌──────────┐┌─────────┐┌─────────┐
              │PostgreSQL││ChromaDB ││  Redis  │
              │          ││(Vectors)││ (Cache) │
              └──────────┘└─────────┘└─────────┘
```

## 📋 Requirements

- **Python 3.14+**
- **uv** (Python package manager)
- **Ollama** (for running LLMs locally)
- **Node.js 20+** (for frontend)
- **PostgreSQL** (optional, SQLite works too)
- **Redis** (for rate limiting)
- **GPU**: NVIDIA GPU with 6GB+ VRAM (RTX 4060 or better) recommended

## 🚀 Quick Start

### 1. Install Prerequisites

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Mistral model
ollama pull mistral:7b-instruct-v0.3-q4_K_M

# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Clone and Setup Backend

```bash
# Clone the repository
cd /home/coller/Desktop/Projects/DocMindAI

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env

# Install Python dependencies
uv sync

# Initialize database
uv run python -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"

# Run backend
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

### 3. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:3000`

### 4. Test the Widget

Create a test HTML file:

```html
<!DOCTYPE html>
<html>
<head>
    <title>DocMind AI Test</title>
</head>
<body>
    <h1>Test Page for DocMind AI Widget</h1>
    
    <!-- Embed the widget -->
    <script 
        src="http://localhost:8000/widget.js" 
        data-business-id="YOUR_BUSINESS_ID">
    </script>
</body>
</html>
```

## 📁 Project Structure

```
DocMindAI/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main application
│   ├── config.py              # Configuration management
│   ├── database.py            # Database models
│   ├── auth.py                # Authentication
│   ├── rag_engine.py          # RAG pipeline
│   ├── rate_limiter.py        # Rate limiting
│   └── schemas.py             # Pydantic schemas
├── frontend/                   # Next.js dashboard
│   ├── app/                   # Next.js 15 app directory
│   ├── components/            # React components
│   └── package.json           # Node dependencies
├── widget/                     # Embeddable chat widget
│   └── widget.js              # Vanilla JavaScript widget
├── data/                       # Data storage
│   └── chroma/                # ChromaDB vector store
├── uploads/                    # Uploaded documents
├── logs/                       # Application logs
├── pyproject.toml             # Python dependencies (uv)
├── docker-compose.yml         # Docker setup
└── README.md                  # This file
```

## 🔧 Configuration

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./docmind.db
# Or PostgreSQL: postgresql+asyncpg://user:pass@localhost:5432/docmind

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b-instruct-v0.3-q4_K_M

# Embedding
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cuda  # or cpu

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-min-32-chars
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get token
- `GET /api/v1/auth/me` - Get current user

### Business Management
- `POST /api/v1/businesses` - Create new business
- `GET /api/v1/businesses` - List all businesses
- `GET /api/v1/businesses/{id}` - Get business details
- `PATCH /api/v1/businesses/{id}` - Update business
- `DELETE /api/v1/businesses/{id}` - Delete business

### Documents
- `POST /api/v1/businesses/{id}/documents` - Upload documents
- `POST /api/v1/businesses/{id}/documents/urls` - Ingest URLs
- `GET /api/v1/businesses/{id}/documents` - List documents
- `DELETE /api/v1/businesses/{id}/documents/{doc_id}` - Delete document

### Chat
- `POST /api/v1/chat/{business_id}` - Send message (public)
- `GET /api/v1/businesses/{id}/widget-config` - Get widget config

### Analytics
- `GET /api/v1/businesses/{id}/analytics` - Get analytics
- `GET /api/v1/businesses/{id}/conversations` - List conversations

## 🐳 Docker Deployment

```bash
# Start all services
docker-compose up -d

# Pull Mistral model in Ollama container
docker exec -it docmind-ollama ollama pull mistral:7b-instruct-v0.3-q4_K_M

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down
```

## 💻 Development

### Run Tests
```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=backend
```

### Code Formatting
```bash
# Format code
uv run black backend/

# Lint code
uv run ruff check backend/

# Type checking
uv run mypy backend/
```

## 🎯 Usage Flow

1. **Register Account** - Create user account via `/register`
2. **Create Business** - Set up your business/chatbot
3. **Upload Documents** - Add PDFs, text files, or website URLs
4. **Customize Widget** - Set bot name, colors, welcome message
5. **Embed Widget** - Copy embed code and add to your website
6. **Monitor Analytics** - Track usage and performance

## 📈 Subscription Plans

| Plan | Price | Queries/Month | Documents | Features |
|------|-------|---------------|-----------|----------|
| **Free** | ₹0 | 50 | 1 | Basic features |
| **Starter** | ₹999 | 1,000 | 10 | Custom branding |
| **Pro** | ₹2,999 | 10,000 | 50 | WhatsApp integration |
| **Enterprise** | ₹9,999 | Unlimited | Unlimited | White-label, API access |

## 🔒 Security Features

- JWT authentication
- Password hashing with bcrypt
- API key authentication for widgets
- Rate limiting per plan
- SQL injection protection
- XSS prevention in widget
- CORS configuration

## ⚡ Performance

- **Response Time**: 2-5 seconds per query
- **Concurrent Users**: 10-20 on RTX 4060
- **Document Processing**: ~1 second per page
- **Vector Search**: Sub-second retrieval
- **Memory Usage**: ~8GB RAM + 5GB VRAM

## 🛠️ Troubleshooting

### Ollama Connection Error
```bash
# Check if Ollama is running
ollama list

# Restart Ollama
sudo systemctl restart ollama
```

### Database Migration
```bash
# If you need to reset database
rm docmind.db
uv run python -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"
```

### GPU Not Detected
```bash
# Check CUDA availability
nvidia-smi

# Set device to CPU in .env
EMBEDDING_DEVICE=cpu
```

### Redis Connection Error
```bash
# Start Redis
sudo systemctl start redis

# Check Redis status
redis-cli ping
```

## 📝 License

MIT License - Feel free to use for commercial purposes

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review the plan.txt for detailed architecture

## 🎉 Acknowledgments

- **FastAPI** - Modern Python web framework
- **LangChain** - RAG framework
- **ChromaDB** - Vector database
- **Ollama** - Local LLM runtime
- **Next.js** - React framework
- **Sentence Transformers** - Embeddings

---

**Built with ❤️ using Python 3.14, FastAPI, ChromaDB, and Next.js**

🚀 Ready to deploy and start making revenue!
