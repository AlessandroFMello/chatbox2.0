from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB: str
    AI_PROVIDER: str  # "gemini" or "openai"
    AI_API_KEY: str
    AI_MODEL: str
    CORS_ORIGINS: str

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
