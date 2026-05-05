from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llama_cloud_api_key: str = ""
    llm_model: str = "openai/gpt-4o"
    database_url: str = "sqlite+aiosqlite:///./finparse.db"
    upload_dir: str = "uploads"

    model_config = {"env_file": ".env"}


settings = Settings()
