from types import TracebackType
from typing import Awaitable, Optional, Type, TypeVar

T = TypeVar("T")


class PostgresRepository:
    """For interacting with a PostgreSQL database through SQLAlchemy"""

    async def __aenter__(self) -> Awaitable[T]:
        # create db connection here
        pass

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Awaitable[Optional[bool]]:
        # close db connection here
        pass
