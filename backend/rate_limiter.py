"""Rate limiting middleware using Redis."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import Business, get_db

settings = get_settings()


class RateLimiter:
    """Rate limiter for API endpoints based on subscription plans."""

    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client: aioredis.Redis | None = None
        self.enabled = settings.rate_limit_enabled

    async def connect(self) -> None:
        """Connect to Redis."""
        if self.enabled:
            try:
                self.redis_client = await aioredis.from_url(
                    settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except Exception as e:
                # If Redis is not available, disable rate limiting
                print(f"Redis connection failed, disabling rate limiting: {e}")
                self.enabled = False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def check_rate_limit(
        self,
        business: Business,
        db: AsyncSession,
    ) -> bool:
        """Check if business has exceeded their rate limit.
        
        Returns:
            True if within limits, False if exceeded
        """
        if not self.enabled:
            return True

        # Get plan limits
        limits = settings.get_plan_limits(business.plan.value)
        max_queries = limits["queries_per_month"]

        # Check current month's usage
        if business.queries_this_month >= max_queries:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Monthly query limit ({max_queries}) exceeded. Please upgrade your plan.",
            )

        return True

    async def increment_usage(
        self,
        business: Business,
        db: AsyncSession,
    ) -> None:
        """Increment the usage counter for a business."""
        business.queries_this_month += 1
        business.total_queries += 1
        await db.commit()

    async def check_document_limit(
        self,
        business: Business,
        db: AsyncSession,
    ) -> bool:
        """Check if business can upload more documents."""
        limits = settings.get_plan_limits(business.plan.value)
        max_documents = limits["max_documents"]

        if business.document_count >= max_documents:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Document limit ({max_documents}) reached. Please upgrade your plan.",
            )

        return True

    async def get_usage_stats(
        self,
        business: Business,
    ) -> dict[str, int | float]:
        """Get usage statistics for a business."""
        limits = settings.get_plan_limits(business.plan.value)
        
        return {
            "queries_used": business.queries_this_month,
            "queries_limit": limits["queries_per_month"],
            "queries_remaining": max(0, limits["queries_per_month"] - business.queries_this_month),
            "usage_percentage": (business.queries_this_month / limits["queries_per_month"]) * 100,
            "documents_used": business.document_count,
            "documents_limit": limits["max_documents"],
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_and_increment_rate_limit(
    business: Business,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Business:
    """Dependency to check rate limits before processing request."""
    await rate_limiter.check_rate_limit(business, db)
    await rate_limiter.increment_usage(business, db)
    return business
