"""Environment and configuration (placeholder)."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"

    # add env vars here


settings = Settings()
