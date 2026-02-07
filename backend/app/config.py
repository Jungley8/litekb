"""
LiteKB 核心配置
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "LiteKB"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"

    # 数据库
    database_url: str = "sqlite:///./data/litekb.db"

    # Qdrant 向量库
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "litekb_chunks"

    # Neo4j 图数据库
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # LLM 配置
    llm_provider: str = "openai"  # openai, ollama, anthropic
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"

    # Embedding 配置
    embedding_provider: str = "openai"  # openai, sentence-transformers
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Chunk 配置
    chunk_size: int = 1000
    chunk_overlap: int = 200

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
