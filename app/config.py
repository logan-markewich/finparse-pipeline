from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llama_cloud_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./finparse.db"
    upload_dir: str = "uploads"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
