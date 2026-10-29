import asyncio
from sqlalchemy import text
from helpers.database import engine


async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version()"))
        print(result.scalar())
    await engine.dispose()


asyncio.run(main())