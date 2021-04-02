from os import environ

from pydantic import BaseConfig


class Settings(BaseConfig):
    """
    This class acts as single-source-of-truth
    for constants definitions and other configuration.
    """

    API_PREFIX: str = environ.get("API_PREFIX", "/api")
    APP_NAME: str = environ.get("APP_NAME", "Apixy")


settings = Settings()
