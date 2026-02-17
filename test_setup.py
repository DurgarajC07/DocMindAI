#!/usr/bin/env python3
"""
Test script to verify DocMind AI installation and functionality.
Run this after setup to ensure everything is working correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_imports():
    """Test that all required packages can be imported."""
    print("✓ Testing package imports...")
    try:
        import fastapi
        import uvicorn
        import chromadb
        import langchain
        import sqlalchemy
        import pydantic
        import sentence_transformers
        print("  ✓ All core packages imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


async def test_database():
    """Test database connection and initialization."""
    print("\n✓ Testing database...")
    try:
        from backend.database import init_db, engine
        from sqlalchemy import text
        
        await init_db()
        print("  ✓ Database initialized successfully")
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("  ✓ Database connection working")
        return True
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False


async def test_config():
    """Test configuration loading."""
    print("\n✓ Testing configuration...")
    try:
        from backend.config import get_settings
        
        settings = get_settings()
        assert settings.app_name == "DocMind AI"
        assert len(settings.secret_key) >= 32
        assert len(settings.jwt_secret_key) >= 32
        print("  ✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


async def test_ollama():
    """Test Ollama connection."""
    print("\n✓ Testing Ollama connection...")
    try:
        import httpx
        from backend.config import get_settings
        
        settings = get_settings()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=10.0
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"  ✓ Ollama is running with {len(models)} models")
                
                # Check for Mistral model
                has_mistral = any("mistral" in m.get("name", "") for m in models)
                if has_mistral:
                    print("  ✓ Mistral model is available")
                else:
                    print("  ⚠ Mistral model not found. Run: ollama pull mistral:7b-instruct-v0.3-q4_K_M")
                return True
            else:
                print(f"  ✗ Ollama returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"  ✗ Ollama connection error: {e}")
        print("  ℹ Make sure Ollama is running: systemctl status ollama")
        return False


async def test_redis():
    """Test Redis connection."""
    print("\n✓ Testing Redis connection...")
    try:
        from redis import asyncio as aioredis
        from backend.config import get_settings
        
        settings = get_settings()
        redis = await aioredis.from_url(settings.redis_url)
        
        # Test ping
        pong = await redis.ping()
        assert pong
        print("  ✓ Redis is running")
        
        await redis.close()
        return True
    except Exception as e:
        print(f"  ✗ Redis connection error: {e}")
        print("  ℹ Make sure Redis is running: sudo systemctl start redis")
        return False


async def test_embeddings():
    """Test embedding model loading."""
    print("\n✓ Testing embedding model...")
    try:
        from sentence_transformers import SentenceTransformer
        from backend.config import get_settings
        
        settings = get_settings()
        
        # Try CUDA first, fall back to CPU
        try:
            model = SentenceTransformer(settings.embedding_model, device="cuda")
            device = "cuda"
        except:
            model = SentenceTransformer(settings.embedding_model, device="cpu")
            device = "cpu"
        
        # Test encoding
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        
        print(f"  ✓ Embedding model loaded successfully on {device}")
        print(f"  ✓ Embedding dimension: {len(embedding)}")
        return True
    except Exception as e:
        print(f"  ✗ Embedding model error: {e}")
        return False


async def test_rag_engine():
    """Test RAG engine initialization."""
    print("\n✓ Testing RAG engine...")
    try:
        from backend.rag_engine import RAGEngine
        
        # Create test engine
        engine = RAGEngine("test_business")
        
        # Get stats
        stats = engine.get_collection_stats()
        print(f"  ✓ RAG engine initialized")
        print(f"  ✓ Collection: {stats['collection_name']}")
        
        # Cleanup
        await engine.delete_collection()
        return True
    except Exception as e:
        print(f"  ✗ RAG engine error: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("DocMind AI - System Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Embeddings", test_embeddings),
        ("Ollama", test_ollama),
        ("Redis", test_redis),
        ("RAG Engine", test_rag_engine),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! DocMind AI is ready to use.")
        print("\nNext steps:")
        print("1. Run: ./run.sh")
        print("2. Open: http://localhost:8000/docs")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
