import abc
from contextlib import asynccontextmanager
from typing import Any, List, AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)

from config import settings
from models import Base


class DatabaseMeta(abc.ABCMeta):
    """Метакласс Singleton"""

    _instances: dict = {}

    def __call__(cls, *args, **kwargs) -> Any:  # type:ignore
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Database(metaclass=DatabaseMeta):
    """Класс предоставляет доступ к engine и фабрике сессий"""

    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.session_maker: AsyncSession | None = None

    async def startup(self) -> None:
        """Используется при запуске приложения"""
        self.engine = create_async_engine(
            settings.MySQL_DATABASE_URL,
            pool_size=100,
            max_overflow=20,
            echo=False,
        )

        self.session_maker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def shutdown(self) -> None:
        if not self.engine:
            raise ValueError
        await self.engine.dispose()


db = Database()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if db.session_maker is None:
        raise RuntimeError("Session maker is not initialized. Call db.startup() first.")

    async with db.session_maker() as async_db_session:
        try:
            yield async_db_session
            await async_db_session.commit()
        except Exception:
            await async_db_session.rollback()
            raise


async def main():
    await db.startup()
    try:
        async with get_session() as session:
            async with session.begin():
                pass
    finally:
        await db.shutdown()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
