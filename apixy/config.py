from os import environ
from typing import Any, Dict, Final, List

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
    DEFAULT_PAGINATION_LIMIT: int = 30

    ORIGINS: List[str] = list(
        map(str.strip, environ.get("CORS_ORIGINS", "*").split(" "))
    )
    ORIGINS_METHODS: List[str] = list(
        map(str.strip, environ.get("CORS_METHODS", "*").split(" "))
    )
    ORIGINS_HEADERS: List[str] = list(
        map(str.strip, environ.get("CORS_HEADERS", "*").split(" "))
    )


SETTINGS = Settings()

TORTOISE_CONFIG: Final[Dict[str, Any]] = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "database": SETTINGS.POSTGRES_DB,
                "host": SETTINGS.POSTGRES_HOST,
                "password": SETTINGS.POSTGRES_PASSWORD,
                "port": SETTINGS.POSTGRES_PORT,
                "user": SETTINGS.POSTGRES_USER,
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
