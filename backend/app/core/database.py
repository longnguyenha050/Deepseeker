import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings

from app.models.models import (
    User, Session, Address, Category, Product, 
    ProductVariantImage, ProductVariant, Promotion, 
    Order, OrderItem, Review, CartItem, Favourite, 
    Post, Contact
)

logger = logging.getLogger(__name__)

async def init_db():
    """
    Initialize a MongoDB connection and load the Beanie Models.
    This function is called in the FastAPI lifespan startup event.
    """
    try:
        client = AsyncIOMotorClient(
            settings.MONGO_URI,
            uuidRepresentation="standard"
        )
        
        db_name = getattr(settings, "MONGO_DB_NAME", "test")
        database = client[db_name]
        
        document_models = [
            User, Session, Address, Category, 
            Product, ProductVariantImage, ProductVariant, 
            Promotion, Order, OrderItem, Review, 
            CartItem, Favourite, Post, Contact
        ]

        await init_beanie(
            database=database,
            document_models=document_models,
            allow_index_dropping=settings.DEBUG  # True if you're in development, False if you're in production.
        )

        await client.admin.command('ping')
        logger.info(f"MongoDB connection to the database was successful: {db_name}")

    except Exception as e:
        logger.error(f"Fatal error when initializing the database.: {str(e)}")
        raise e