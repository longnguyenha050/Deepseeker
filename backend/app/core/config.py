from typing import List, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Shate Shop RAG System"
    API_V1_STR: str = "/api/v1"

    DEBUG: bool = False

    # --- DATABASE (MongoDB) ---
    MONGO_URI: str
    MONGO_DB_NAME: str = "test"

    DOC_DIRECTORY: str = "../data/contextual_docs.json"
    RERANK_TOP_N: int = 3

    ALLOWED_COLLECTIONS: list = [
        # "orderitems",
        "productvariants",
        "products",
        "promotions",
    ]

    # --- SECURITY (JWT) ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 ngày

    # --- CORS (Cross-Origin Resource Sharing) ---
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # --- CLOUDINARY ---
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    # --- RAG & AI (OpenAI / Vector DB) ---
    OPENAI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
