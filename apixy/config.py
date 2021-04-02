from os import environ

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
