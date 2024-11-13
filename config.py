import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore
    model_config = SettingsConfigDict(extra="ignore", env_file=".env")
    PASSWORD_SALT_ROUNDS: int = 12
    ACCESS_TOKEN_LIFETIME_MINUTES: int = int(os.getenv("ACCESS_TOKEN_LIFETIME_MINUTES", 120))
    REFRESH_TOKEN_LIFETIME_DAYS: int = int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", 30))
    ALGORITHM: str = "HS512"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret")

    MySQL_DATABASE_URL: str = f"mysql+aiomysql://root:pass@26.143.23.99:3306/swe_csci361"


settings = Settings()
