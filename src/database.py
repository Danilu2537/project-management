# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from settings import settings
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DATABASE_URL)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
