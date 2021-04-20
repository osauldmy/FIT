from os import environ
from typing import Any, Dict, Final

from pydantic import BaseConfig


class Settings(BaseConfig):
    """
    This class acts as single-source-of-truth
    for constants definitions and other configuration.
    """

    API_PREFIX: str = environ.get("API_PREFIX", "/api")
    APP_NAME: str = environ.get("APP_NAME", "Apixy")
    POSTGRES_DB: str = environ.get("POSTGRES_DB", "")
    POSTGRES_HOST: str = environ.get("POSTGRES_HOST", "")
    POSTGRES_PORT: str = environ.get("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = environ.get("POSTGRES_USER", "")
    POSTGRES_PASSWORD: str = environ.get("POSTGRES_PASSWORD", "")


settings = Settings()


TORTOISE_CONFIG: Final[Dict[str, Any]] = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "database": settings.POSTGRES_DB,
                "host": settings.POSTGRES_HOST,
                "password": settings.POSTGRES_PASSWORD,
                "port": settings.POSTGRES_PORT,
                "user": settings.POSTGRES_USER,
            },
        }
    },
    "apps": {
        "models": {
            "models": [
                "apixy.models",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
}
