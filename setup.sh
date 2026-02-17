#!/bin/bash

# DocMind AI - Setup and Run Script
# This script sets up and runs the complete DocMind AI application

set -e

echo "🚀 DocMind AI - Setup and Run Script"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in project directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo ""
echo "Step 1: Checking prerequisites..."
echo "--------------------------------"

# Check Python
if command -v python3.14 &> /dev/null; then
    echo -e "${GREEN}✓ Python 3.14 found${NC}"
else
    echo -e "${YELLOW}⚠ Python 3.14 not found. Please install Python 3.14+${NC}"
fi

# Check uv
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ uv found${NC}"
else
    echo -e "${YELLOW}⚠ uv not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama found${NC}"
else
    echo -e "${YELLOW}⚠ Ollama not found. Please install from https://ollama.com${NC}"
    echo "Run: curl -fsSL https://ollama.com/install.sh | sh"
fi

# Check Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠ Redis not running. Starting Redis...${NC}"
        sudo systemctl start redis 2>/dev/null || echo "Please start Redis manually"
    fi
else
    echo -e "${YELLOW}⚠ Redis not found. Install: sudo apt-get install redis-server${NC}"
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js found ($(node --version))${NC}"
else
    echo -e "${YELLOW}⚠ Node.js not found. Please install Node.js 20+${NC}"
fi

echo ""
echo "Step 2: Setting up environment..."
echo "--------------------------------"

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    
    # Generate secret keys
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update secret keys in .env
    sed -i "s/your-super-secret-key-change-this-in-production-min-32-chars/$SECRET_KEY/" .env
    sed -i "s/your-jwt-secret-key-change-this-in-production-min-32-chars/$JWT_SECRET_KEY/" .env
    
    echo -e "${GREEN}✓ .env file created with secure secret keys${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""
echo "Step 3: Installing Python dependencies..."
echo "----------------------------------------"

uv sync

echo -e "${GREEN}✓ Python dependencies installed${NC}"

echo ""
echo "Step 5: Initializing database..."
echo "--------------------------------"

uv run python3 -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"

echo -e "${GREEN}✓ Database initialized${NC}"

echo ""
echo "Step 6: Seeding database with sample data..."
echo "-------------------------------------------"

read -p "Do you want to add sample data (demo users & businesses)? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    uv run python3 seed_db.py
    echo -e "${GREEN}✓ Database seeded with sample data${NC}"
else
    echo "Skipping database seeding"
fi

echo ""
echo "Step 7: Checking Ollama models..."
echo "--------------------------------"

if ollama list | grep -q "mistral"; then
    echo -e "${GREEN}✓ Mistral model already downloaded${NC}"
else
    echo -e "${YELLOW}Downloading Mistral model (this may take a while)...${NC}"
    ollama pull mistral:7b-instruct-v0.3-q4_K_M
    echo -e "${GREEN}✓ Mistral model downloaded${NC}"
fi

echo ""
echo "Step 5: Initializing database..."
echo "--------------------------------"

uv run python3 -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"

echo -e "${GREEN}✓ Database initialized${NC}"

echo ""
echo "Step 8: Setting up frontend..."
echo "-----------------------------"

if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
    fi
    cd ..
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo "======================================"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 - Backend:"
echo "  uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2 - Frontend (optional):"
echo "  cd frontend && npm run dev"
echo ""
echo "Then open:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "Or use the run script:"
echo "  ./run.sh"
echo ""
