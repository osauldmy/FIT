from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter
from fastapi.types import DecoratedCallable
from starlette import status
from starlette.responses import Response
from tortoise.functions import Avg

from apixy.config import SETTINGS
from apixy.entities.datasource import DataSourceFetchLogSummary
from apixy.entities.project import FetchLogger
from apixy.models import DataSourceModel, FetchLogModel


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
        self,
        datasource_id: int,
        nanoseconds: int,
        fetch_status: FetchLogger.FetchStatus,
    ) -> None:
        await FetchLogModel.create(
            datasource=await DataSourceModel.get(id=datasource_id),
            nanoseconds=nanoseconds,
            status=fetch_status,
        )

    @classmethod
    async def get_stats(cls, datasource_id: int) -> DataSourceFetchLogSummary:
        queryset = FetchLogModel.filter(datasource_id=datasource_id)
        total = await queryset.count()
        return DataSourceFetchLogSummary(
            calls=total,
            average_success_time=cls.ns_to_ms(
                await queryset.filter(status=FetchLogger.FetchStatus.SUCCESS)
                .group_by()
                .annotate(average_time=Avg("nanoseconds"))
                .first()
                .values_list("average_time", flat=True),
            ),
            success_rate=cls.percentage_of(
                await queryset.filter(status=FetchLogger.FetchStatus.SUCCESS).count(),
                total,
            ),
            timeout_rate=cls.percentage_of(
                await queryset.filter(status=FetchLogger.FetchStatus.TIMEOUT).count(),
                total,
            ),
            error_rate=cls.percentage_of(
                await queryset.filter(status=FetchLogger.FetchStatus.ERROR).count(),
                total,
            ),
            first_call=cls.first_of_list(
                await queryset.order_by("created")
                .first()
                .values_list("created", flat=True),
            ),
            last_call=cls.first_of_list(
                await queryset.order_by("-created")
                .first()
                .values_list("created", flat=True),
            ),
        )

    @staticmethod
    def percentage_of(value: int, total_count: int) -> Optional[float]:
        if total_count == 0:
            return None
        return 100 * value / total_count

    @staticmethod
    def first_of_list(value: List[Any]) -> Any:
        return value[0] if len(value) > 0 else None

    @staticmethod
    def ns_to_ms(values: List[Optional[float]]) -> Optional[float]:
        if len(values) == 0:
            return None
        if values[0] is None:
            return None
        return values[0] * 1e-6


async def get_fetch_logger() -> DBFetchLogger:
    return DBFetchLogger()
