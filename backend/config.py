from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://moviepicker:password@localhost:5432/moviepicker"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Set this env var to bypass OTP in tests (e.g., TEST_OTP_CODE=123456)
    test_otp_code: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
