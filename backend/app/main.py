from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    pass

# 2. Khởi tạo FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def health_check():
    return {
        "app_name": settings.PROJECT_NAME,
        "status": "active", 
        "database": "connected"
    }

# Endpoint ví dụ lấy danh sách User để test model
from app.models.models import User
from typing import List

@app.get("/users", response_model=List[User])
async def get_users():
    # Beanie query rất giống Mongo
    users = await User.find_all().to_list()
    return users