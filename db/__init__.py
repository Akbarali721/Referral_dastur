from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///referral.db")
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
