from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    DB_ECHO: bool = False
    
    SECRET_KEY: str = "your-secret-key-for-dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 2

    REDIS_URL: str = "redis://redis:6379/0"

    RATE_LIMIT_AUTH_USER: int = 1000
    RATE_LIMIT_GUEST_USER: int = 200

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

settings = Settings()
