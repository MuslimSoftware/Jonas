from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.features.user.models import User
from .env import settings

async def init_db():
    """Initialize database connection."""
    # Create Motor client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize beanie with the MongoDB client and document models
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[User]
    )
    
    return client 