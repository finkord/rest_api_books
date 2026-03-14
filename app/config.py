from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration settings."""
    mongodb_url: str = "mongodb://admin:adminpassword@localhost:27017"
    mongodb_db_name: str = "library"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
