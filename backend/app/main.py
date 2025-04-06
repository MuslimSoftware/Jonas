from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config.env import settings
from app.config.db_config import init_db
from app.config.redis_config import init_redis_pool, close_redis_pool
from app.features.auth.controllers import auth_controller
from app.features.common.exceptions import AppException
from app.middlewares import app_exception_handler, global_exception_handler
from app.config.logging import setup_logging
from app.config.rate_limit import limiter 
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import contextlib
from app.middlewares.redis_middleware import RedisMiddleware

# Initialize rate limiter - REMOVED (now imported)
# limiter = Limiter(key_func=get_remote_address)

# Updated lifespan function
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis_pool() # Initialize Redis pool
    print("Database and Redis pool initialized.") # Log for confirmation
    yield
    # Clean up resources
    await close_redis_pool() # Close Redis pool
    print("Redis pool closed.") # Log for confirmation

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan,
)

# Setup rate limiting state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

setup_logging()

# Handler for custom app exceptions
app.add_exception_handler(AppException, app_exception_handler)

# Handler for all other unhandled exceptions
app.add_exception_handler(Exception, global_exception_handler)

# Add rate limiting middleware BEFORE other middlewares/routes if you want it applied first
app.add_middleware(SlowAPIMiddleware)

# Add Redis Middleware (doesn't need client instance passed anymore)
app.add_middleware(RedisMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with global API prefix
api_prefix = f"{settings.API_PREFIX}{settings.API_VERSION_PREFIX}"
app.include_router(auth_controller.router, prefix=api_prefix)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the API"} 

# TODO: Implement test controller with test endpoints
@app.get(f"{api_prefix}/test-app-exception")
async def test():
    raise AppException(message="Test error", error_code="TEST_ERROR", status_code=400)

@app.get(f"{api_prefix}/test-global-exception")
async def test():
    raise Exception("Test error")