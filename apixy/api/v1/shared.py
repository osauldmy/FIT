from typing import Any, Callable

from fastapi import APIRouter
from fastapi.types import DecoratedCallable
from starlette import status
from starlette.responses import Response


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
