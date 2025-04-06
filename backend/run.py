import uvicorn
from app.config.env import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True  # Enable auto-reload during development
    ) 