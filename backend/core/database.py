from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.product_model import Product
from app.core.config import settings

async def init_db():
    # Tạo client kết nối (Async)
    client = AsyncIOMotorClient(settings.MONGO_URI)
    
    # Chỉ định database name
    db = client.test
    
    # Khởi tạo Beanie với list các models
    await init_beanie(database=db, document_models=[Product])