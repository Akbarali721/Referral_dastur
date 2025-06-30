import asyncio
from db import engine
from db.models import Base  # Base va model faylingizni to‘g‘ri joydan import qiling

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Baza jadvallari yaratildi")

if __name__ == "__main__":
    asyncio.run(init_db())
