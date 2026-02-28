from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes

from app.core.config import settings
from app.core.database import init_db
from app.models.models import User
from app.utils.schema_helper import get_all_schemas
from app.schemas import GraphInput
from app.graph.workflow import app_graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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

@app.get("/users", response_model=List[User])
async def get_users():
    users = await User.find_all().to_list()
    return users

@app.get("/db_schema", response_model=str)
async def get_db_schema():
    return get_all_schemas()

typed_graph = app_graph.with_types(input_type=GraphInput)

add_routes(
    app,
    typed_graph,
    path="/rag",
    # Tắt bật playground trên production
    playground_type="default", 
)
