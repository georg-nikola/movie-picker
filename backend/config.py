from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://moviepicker:password@localhost:5432/moviepicker"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7


    class Config:
        env_file = ".env"


settings = Settings()
