"""Environment and configuration.

Expose `DB_URL` (env var: `DB_URL`) used by database engine.
"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    DB_URL: str = "sqlite:///./dev.db"

    class Config:
        env_file = ".env"


settings = Settings()
