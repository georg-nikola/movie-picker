from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://moviepicker:password@localhost:5432/moviepicker"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_must_be_set(cls, v: str) -> str:
        if v == "change-me-in-production":
            raise ValueError(
                "JWT_SECRET environment variable must be set to a strong random secret"
            )
        return v

    class Config:
        env_file = ".env"


settings = Settings()
