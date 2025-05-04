from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.features.user.models import User
from app.features.chat.models import Chat, Message, Screenshot, ContextItem
from .env import settings

# Add imports for SQLAlchemy and logging
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool

# Import pymongo for external connection
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ConnectionFailure

logger = logging.getLogger(__name__)

# --- MongoDB / Beanie Initialization ---
async def init_db():
    """Initialize MongoDB database connection using Beanie."""
    # Create Motor client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    # Initialize beanie with the MongoDB client and document models
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[User, Chat, Message, Screenshot, ContextItem]
    )
    logger.info(f"Beanie initialized with MongoDB: {settings.MONGODB_DB_NAME}")
    return client

# --- External MongoDB Client Initialization (using pymongo) ---
external_mongo_client = None
external_mongo_db = None

def init_external_mongo_client():
    """Initialize the PyMongo client for the external MongoDB database."""
    global external_mongo_client, external_mongo_db
    if external_mongo_client is not None:
        logger.warning("External PyMongo client already initialized.")
        return external_mongo_client, external_mongo_db

    if not settings.FH_MONGO_URI or not settings.FH_MONGO_DB_NAME:
        logger.warning("External FH MongoDB URI or DB Name not configured. Skipping initialization.")
        return None, None

    try:
        external_mongo_client = MongoClient(settings.FH_MONGO_URI, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        external_mongo_client.admin.command('ismaster')
        external_mongo_db = external_mongo_client[settings.FH_MONGO_DB_NAME]
        logger.info(f"External PyMongo client initialized for DB: {settings.FH_MONGO_DB_NAME}")
    except ConfigurationError as e:
        logger.critical(f"Failed to initialize External PyMongo client (Configuration Error): {e}", exc_info=True)
        external_mongo_client = None
        external_mongo_db = None
    except ConnectionFailure as e:
        logger.critical(f"Failed to connect to External MongoDB server: {e}", exc_info=True)
        external_mongo_client = None
        external_mongo_db = None
    except Exception as e:
        logger.critical(f"An unexpected error occurred during External PyMongo client initialization: {e}", exc_info=True)
        external_mongo_client = None
        external_mongo_db = None
        
    return external_mongo_client, external_mongo_db

def get_external_mongo_db():
    """Returns the initialized external MongoDB database object."""
    if external_mongo_db is None:
        logger.error("External MongoDB database requested but not initialized. Call init_external_mongo_client() during startup.")
    return external_mongo_db

# --- SQLAlchemy Engine Initialization ---
sql_engine = None

def init_sql_engine():
    """Initialize the SQLAlchemy engine and connection pool for MySQL."""
    global sql_engine # Allow modification of the global variable
    if sql_engine is not None:
        logger.warning("SQLAlchemy engine already initialized.")
        return sql_engine
        
    # Construct the database URL from settings
    # Ensure correct format: mysql+mysqlconnector://user:password@host:port/database
    DATABASE_URL = (
        f"mysql+mysqlconnector://{settings.FH_USER}:{settings.FH_PASSWORD}"
        f"@{settings.FH_HOST}:{settings.FH_PORT}/{settings.FH_DB_NAME}"
    )

    try:
        # Create the SQLAlchemy engine
        sql_engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.FH_SQL_POOL_SIZE, # Get from settings
            max_overflow=settings.FH_SQL_MAX_OVERFLOW, # Get from settings
            pool_timeout=30,
            pool_recycle=1800,
            echo=settings.FH_SQL_ECHO # Get from settings (False for prod)
        )
        logger.info(f"SQLAlchemy engine created successfully for {settings.FH_HOST}:{settings.FH_PORT}/{settings.FH_DB_NAME}")
        
        # Optional: Test connection on startup (can be noisy)
        # with sql_engine.connect() as connection:
        #    logger.info("SQLAlchemy engine connected successfully on startup.")
            
    except SQLAlchemyError as e:
        logger.critical(f"Failed to create SQLAlchemy engine: {e}", exc_info=True)
        sql_engine = None # Ensure engine is None if creation failed
    except Exception as e:
        logger.critical(f"An unexpected error occurred during SQLAlchemy engine creation: {e}", exc_info=True)
        sql_engine = None
        
    return sql_engine

def get_sql_engine():
    """Returns the initialized SQLAlchemy engine. Initializes if not already done."""
    # Simple getter, assumes init_sql_engine is called during app startup
    if sql_engine is None:
        logger.error("SQLAlchemy engine requested but not initialized. Call init_sql_engine() during startup.")
        # Depending on requirements, could attempt initialization here, but better at startup
        # init_sql_engine()
        # if sql_engine is None:
        #    raise RuntimeError("SQLAlchemy engine failed to initialize.")
    return sql_engine