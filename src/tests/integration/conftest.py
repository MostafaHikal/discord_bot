import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from helpers.config import get_settings


@pytest_asyncio.fixture
async def session():
    settings = get_settings()

    # 1. the test URL must exist
    if not settings.TEST_DATABASE_URL:
        pytest.fail("TEST_DATABASE_URL is not set in .env")

    # 2. refuse to run if it points at the main database (we wipe tables below)
    test_url = make_url(settings.TEST_DATABASE_URL)
    main_url = make_url(settings.DATABASE_URL)
    if (test_url.host, test_url.database) == (main_url.host, main_url.database):
        pytest.exit("TEST_DATABASE_URL points at the main database", returncode=1)

    # NullPool: no connection reuse, each test opens and closes its own
    engine = create_async_engine(settings.TEST_DATABASE_URL, poolclass=NullPool)

    # 3. every test starts with an empty users table
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY"))

    # 4. hand a session to the test, close everything when it finishes
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session

    await engine.dispose()