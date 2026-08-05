from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "OpsPilot"

    database_url: str = "postgresql+asyncpg://opspilot:opspilot@localhost:5432/opspilot"

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "changeme-generate-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    cors_allowed_origins: str = "http://localhost:3000"

    # --- Uploads / ingestion (Phase 3, SECURITY.md §19-22) ---
    upload_base_dir: str = "var/uploads"
    upload_max_size_bytes: int = 25 * 1024 * 1024  # 25 MB

    # --- Embeddings / RAG (Phase 4, ADR-025) ---
    gemini_api_key: str = "changeme-your-gemini-api-key"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 768

    # --- Chunking (RAG_SYSTEM.md §9) ---
    chunk_target_tokens: int = 550
    chunk_overlap_tokens: int = 75

    # --- Retrieval (RAG_SYSTEM.md §19) ---
    retrieval_candidate_limit: int = 15

    # --- Reranking (RAG_SYSTEM.md §22, ADR-030) ---
    reranker_model: str = "gemini-flash-latest"

    # --- Context selection (RAG_SYSTEM.md §25) ---
    # Deliberately bounded well below typical model context windows — "do not
    # fill the context window merely because capacity exists."
    context_token_budget: int = 4000

    # --- LLM generation (Phase 5, ADR-031) ---
    llm_model: str = "gemini-flash-latest"

    # --- Analytics SQL execution (Phase 5, ADR-032, SECURITY.md §10-14) ---
    analytics_readonly_role: str = "opspilot_analytics_ro"
    analytics_max_result_rows: int = 500
    analytics_query_timeout_seconds: float = 5.0
    # ANALYTICS_ENGINE.md §28: "allow one/few bounded correction attempts".
    analytics_max_sql_generation_attempts: int = 2

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
