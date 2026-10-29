"""
Database engine and session factory — plan Phase 2.

Owns the single async Engine (connection pool to Neon) and how a Session
is opened per request. Thin on purpose: it knows how to connect and hand
out sessions, nothing about tables or queries (models/, controllers/).
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from helpers.config import get_settings

settings = get_settings()

# Module-level singleton for now: one pool for the whole app is the
# simplest thing that works. Trade-off: tests can't swap in a separate
# test database without patching this module. If that becomes painful in
# Phase 2 testing, we turn this into a create_database() factory.
engine = create_async_engine(
    settings.DATABASE_URL,
    # Neon suspends idle compute, which silently kills pooled connections.
    # Without this, the first request after a quiet period can fail on a
    # dead connection. The cost is one tiny round-trip per checkout.
    pool_pre_ping=True,
)

# expire_on_commit=False: by default SQLAlchemy marks every object stale
# after commit, and reading a stale attribute triggers a lazy reload.
# Async sessions can't do that implicitly, so it raises MissingGreenlet.
# Keeping objects readable after commit avoids that.
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_session():
    # Yield one Session per request; closed (connection returned to the pool) afterwards.
    async with SessionLocal() as session:
        yield session