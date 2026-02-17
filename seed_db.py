#!/usr/bin/env python3
"""
Seed script to populate DocMind AI database with sample data.
Run this to create demo users, businesses, and documents for testing.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


async def seed_database():
    """Seed the database with sample data."""
    from backend.database import get_db, User, Business, Document, Conversation, init_db, PlanType
    from backend.auth import get_password_hash
    from sqlalchemy import select
    
    print("🌱 Seeding DocMind AI Database...")
    print("=" * 50)
    
    # Initialize database first
    await init_db()
    print("✓ Database initialized")
    
    # Get database session
    async for db in get_db():
        try:
            # Check if data already exists
            result = await db.execute(select(User).where(User.email == "demo@docmind.ai"))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("\n⚠ Sample data already exists. Skipping seed.")
                print("  To re-seed, delete docmind.db and run again.")
                return
            
            print("\n1. Creating demo users...")
            
            # Create demo users
            demo_user = User(
                id=str(uuid.uuid4()),
                email="demo@docmind.ai",
                full_name="Demo User",
                hashed_password=get_password_hash("demo123"),
                is_active=True,
            )
            db.add(demo_user)
            
            admin_user = User(
                id=str(uuid.uuid4()),
                email="admin@docmind.ai",
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
            )
            db.add(admin_user)
            
            await db.flush()
            print(f"  ✓ Created user: {demo_user.email} (password: demo123)")
            print(f"  ✓ Created user: {admin_user.email} (password: admin123)")
            
            print("\n2. Creating sample businesses...")
            
            # Business 1: Tech Startup
            tech_business = Business(
                id=str(uuid.uuid4()),
                owner_id=demo_user.id,
                name="TechStart AI",
                description="AI-powered software development company",
                website="https://techstart.ai",
                plan=PlanType.PRO,
                api_key=str(uuid.uuid4()),
                bot_name="TechBot",
                welcome_message="Hi! I'm TechBot. How can I help you with our AI solutions?",
                theme_color="#2563eb",
                is_active=True,
                document_count=0,
                queries_this_month=0,
                total_queries=0,
            )
            db.add(tech_business)
            
            # Business 2: E-commerce Store
            ecom_business = Business(
                id=str(uuid.uuid4()),
                owner_id=demo_user.id,
                name="ShopSmart",
                description="Online retail store for electronics",
                website="https://shopsmart.com",
                plan=PlanType.STARTER,
                api_key=str(uuid.uuid4()),
                bot_name="ShopAssistant",
                welcome_message="Welcome to ShopSmart! How can I assist you today?",
                theme_color="#10b981",
                is_active=True,
                document_count=0,
                queries_this_month=0,
                total_queries=0,
            )
            db.add(ecom_business)
            
            # Business 3: Consulting Firm
            consult_business = Business(
                id=str(uuid.uuid4()),
                owner_id=admin_user.id,
                name="Elite Consulting",
                description="Business strategy and management consulting",
                website="https://eliteconsult.com",
                plan=PlanType.ENTERPRISE,
                api_key=str(uuid.uuid4()),
                bot_name="ConsultBot",
                welcome_message="Hello! I'm here to answer your questions about our consulting services.",
                theme_color="#8b5cf6",
                is_active=True,
                document_count=0,
                queries_this_month=0,
                total_queries=0,
            )
            db.add(consult_business)
            
            await db.flush()
            print(f"  ✓ Created business: {tech_business.name}")
            print(f"  ✓ Created business: {ecom_business.name}")
            print(f"  ✓ Created business: {consult_business.name}")
            
            print("\n3. Creating sample documents...")
            
            # Documents for TechStart AI
            doc1 = Document(
                id=str(uuid.uuid4()),
                business_id=tech_business.id,
                filename="company_overview.txt",
                file_path="uploads/demo/company_overview.txt",
                file_size=1024,
                file_type=".txt",
                is_processed=True,
                chunks_count=5,
            )
            db.add(doc1)
            tech_business.document_count += 1
            
            doc2 = Document(
                id=str(uuid.uuid4()),
                business_id=tech_business.id,
                filename="pricing_plans.pdf",
                file_path="uploads/demo/pricing.pdf",
                file_size=2048,
                file_type=".pdf",
                is_processed=True,
                chunks_count=8,
            )
            db.add(doc2)
            tech_business.document_count += 1
            
            # Documents for ShopSmart
            doc3 = Document(
                id=str(uuid.uuid4()),
                business_id=ecom_business.id,
                filename="product_catalog.txt",
                file_path="uploads/demo/products.txt",
                file_size=3072,
                file_type=".txt",
                is_processed=True,
                chunks_count=12,
            )
            db.add(doc3)
            ecom_business.document_count += 1
            
            print(f"  ✓ Created 3 sample documents")
            
            print("\n4. Creating sample conversations...")
            
            # Sample conversations for TechStart AI
            conv1 = Conversation(
                id=str(uuid.uuid4()),
                business_id=tech_business.id,
                session_id="demo_session_1",
                user_message="What services do you offer?",
                bot_response="We offer AI-powered software development, machine learning consulting, and custom chatbot solutions for businesses.",
                user_feedback=1,
                sources_used=2,
                was_answered=True,
                response_time_ms=1500,
                created_at=datetime.now() - timedelta(days=2),
            )
            db.add(conv1)
            tech_business.queries_this_month += 1
            tech_business.total_queries += 1
            
            conv2 = Conversation(
                id=str(uuid.uuid4()),
                business_id=tech_business.id,
                session_id="demo_session_1",
                user_message="What are your pricing plans?",
                bot_response="We have three pricing tiers: Starter at $99/month, Professional at $299/month, and Enterprise with custom pricing.",
                user_feedback=1,
                sources_used=3,
                was_answered=True,
                response_time_ms=1800,
                created_at=datetime.now() - timedelta(days=2, hours=1),
            )
            db.add(conv2)
            tech_business.queries_this_month += 1
            tech_business.total_queries += 1
            
            conv3 = Conversation(
                id=str(uuid.uuid4()),
                business_id=tech_business.id,
                session_id="demo_session_2",
                user_message="How can I contact support?",
                bot_response="You can reach our support team at support@techstart.ai or call us at 1-800-TECH-AI.",
                sources_used=1,
                was_answered=True,
                response_time_ms=1200,
                created_at=datetime.now() - timedelta(days=1),
            )
            db.add(conv3)
            tech_business.queries_this_month += 1
            tech_business.total_queries += 1
            
            # Sample conversations for ShopSmart
            conv4 = Conversation(
                id=str(uuid.uuid4()),
                business_id=ecom_business.id,
                session_id="demo_session_3",
                user_message="Do you have laptops in stock?",
                bot_response="Yes! We have a wide range of laptops from brands like Dell, HP, and Lenovo. Prices start at $499.",
                user_feedback=1,
                sources_used=2,
                was_answered=True,
                response_time_ms=1400,
                created_at=datetime.now() - timedelta(hours=5),
            )
            db.add(conv4)
            ecom_business.queries_this_month += 1
            ecom_business.total_queries += 1
            
            conv5 = Conversation(
                id=str(uuid.uuid4()),
                business_id=ecom_business.id,
                session_id="demo_session_3",
                user_message="What's your return policy?",
                bot_response="We offer a 30-day return policy on all electronics. Items must be in original condition with all packaging.",
                user_feedback=-1,
                sources_used=1,
                was_answered=True,
                response_time_ms=1100,
                created_at=datetime.now() - timedelta(hours=4),
            )
            db.add(conv5)
            ecom_business.queries_this_month += 1
            ecom_business.total_queries += 1
            
            print(f"  ✓ Created 5 sample conversations")
            
            # Commit all changes
            await db.commit()
            
            print("\n" + "=" * 50)
            print("✅ Database seeded successfully!")
            print("=" * 50)
            
            print("\n📊 Summary:")
            print(f"  • Users: 2")
            print(f"  • Businesses: 3")
            print(f"  • Documents: 3")
            print(f"  • Conversations: 5")
            
            print("\n🔑 Demo Credentials:")
            print("=" * 50)
            print("User 1:")
            print(f"  Email: demo@docmind.ai")
            print(f"  Password: demo123")
            print(f"  Businesses: TechStart AI, ShopSmart")
            print()
            print("User 2:")
            print(f"  Email: admin@docmind.ai")
            print(f"  Password: admin123")
            print(f"  Businesses: Elite Consulting")
            
            print("\n🌐 Next Steps:")
            print("  1. Start the application: ./run.sh")
            print("  2. Visit: http://localhost:3001")
            print("  3. Login with demo credentials above")
            print("  4. Explore the pre-populated data!")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error seeding database: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            break  # Exit after first iteration


if __name__ == "__main__":
    try:
        asyncio.run(seed_database())
    except KeyboardInterrupt:
        print("\n\n⚠ Seeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
