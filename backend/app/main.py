from fastapi import FastAPI
from app.config.env import settings
from app.config.db_config import init_db, init_sql_engine, init_external_mongo_client
from app.config.redis_config import init_redis_pool, close_redis_pool
from app.features.auth.controllers import auth_controller
from app.features.chat.controllers import chat_controller
from app.middlewares import setup_middleware, setup_exception_handlers
from app.config.logging import setup_logging
from app.config.rate_limit import limiter
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis_pool()
    init_sql_engine()
    init_external_mongo_client()
    yield
    await close_redis_pool()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# Setup rate limiting state
app.state.limiter = limiter

setup_exception_handlers(app)

# Setup logging AFTER exception handlers are attached
setup_logging()

# Setup middlewares
setup_middleware(app)

# Include routers with global API prefix
api_prefix = f"{settings.API_PREFIX}{settings.API_VERSION_PREFIX}"
app.include_router(auth_controller.router, prefix=api_prefix)
app.include_router(chat_controller.router, prefix=api_prefix)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the API"}