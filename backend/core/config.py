from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fitness"
    MONGO_URL: str = "mongodb://root:example@localhost:27017"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    JWT_SECRET: str = "supersecretkey"
    JWT_ALGORITHM: str = "HS256"
    OPENAI_API_KEY: str = "dummy"
    
    HUAWEI_CLIENT_ID: str = "dummy_huawei_client_id"
    HUAWEI_CLIENT_SECRET: str = "dummy_huawei_client_secret"
    HUAWEI_ENCRYPTION_KEY: str = "VlY4K2R-xK8pL7_T4X_8H9Q3jJ1V7r4Z6X1M0Q8W9Uo="

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
