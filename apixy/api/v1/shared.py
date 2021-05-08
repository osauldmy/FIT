from typing import Any, Callable, Dict

from fastapi import APIRouter
from fastapi.types import DecoratedCallable
from starlette import status
from starlette.responses import Response

from apixy.config import SETTINGS
from apixy.entities.project import FetchLogger
from apixy.models import FetchLogModel


class ApixyRouter(APIRouter):
    """
    A drop-in replacement for fastapi.APIRouter,
    allowing for easy customisation of its defaults.
    """

    def post(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        kwargs["status_code"] = kwargs.get("status_code", status.HTTP_201_CREATED)
        kwargs["response_class"] = kwargs.get("response_class", Response)
        return super().post(*args, **kwargs)

    def put(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        kwargs["status_code"] = kwargs.get("status_code", status.HTTP_204_NO_CONTENT)
        kwargs["response_class"] = kwargs.get("response_class", Response)
        return super().put(*args, **kwargs)

    def delete(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        kwargs["status_code"] = kwargs.get("status_code", status.HTTP_204_NO_CONTENT)
        kwargs["response_class"] = kwargs.get("response_class", Response)
        return super().delete(*args, **kwargs)


async def pagination_params(
    limit: int = SETTINGS.DEFAULT_PAGINATION_LIMIT, offset: int = 0
) -> Dict[str, int]:
    return {"limit": limit, "offset": offset}


class DBFetchLogger(FetchLogger):
    async def save_log(
        self, datasource_id: int, nanoseconds: int, success: bool
    ) -> None:
        await FetchLogModel.create(
            datasource_id=datasource_id, time=nanoseconds, success=success
        )


async def fetch_logger() -> DBFetchLogger:
    return DBFetchLogger()
