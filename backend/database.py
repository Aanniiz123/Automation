from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from dotenv import load_dotenv
import os


load_dotenv()

Base = declarative_base()

engine = create_async_engine(os.getenv("DATABASE_URL"), echo=True)
session = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


async def get_db():
    async with session() as db:
        try:
            yield db
        finally:
            await db.close()