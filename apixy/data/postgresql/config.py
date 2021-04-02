from typing import Any, Dict, Final

from apixy.config import settings

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
                "apixy.data.postgresql.models.core",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
}
