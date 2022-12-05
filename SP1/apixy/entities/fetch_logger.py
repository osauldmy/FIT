from __future__ import annotations

import asyncio
import time
from abc import abstractmethod
from datetime import datetime
from enum import IntEnum, auto
from functools import wraps
from typing import Any, Awaitable, Callable, Optional, Tuple

from pydantic import Field

from apixy.entities.datasource import DataSourceFetchError
from apixy.entities.shared import ForbidExtraModel


class FetchLogger:
    class FetchStatus(IntEnum):
        SUCCESS = auto()
        TIMEOUT = auto()
        ERROR = auto()

    @abstractmethod
    async def save_log(
        self,
        datasource_id: int,
        nanoseconds: int,
        fetch_status: FetchLogger.FetchStatus,
    ) -> None:
        """Adds a log entry about a fetch attempt."""

    @abstractmethod
    async def get_stats(self, datasource_id: int) -> DataSourceFetchLogSummary:
        """Aggregates statistics from logs."""

    @staticmethod
    def fetch_timer(coroutine: Callable[[], Awaitable[Any]]) -> Any:
        """
        A decorator-like utility for timing the called fetch coroutine.
        :param coroutine: the fetch method to call
        :return: the wrapped coroutine's awaited result along with time in nanoseconds
        """

        @wraps(coroutine)
        async def wrapped() -> Tuple[Any, int]:
            time_start = time.perf_counter_ns()
            try:
                result = await coroutine()
            except (asyncio.TimeoutError, DataSourceFetchError) as exc:
                result = exc
            time_measured = time.perf_counter_ns() - time_start
            return result, time_measured

        # not returning a callable but the actual result here
        # that is to allow for using this in asyncio.wait/asyncio.gather
        return wrapped()


class DataSourceFetchLogSummary(ForbidExtraModel):
    """A summary of fetch attempts on this DataSource."""

    calls: int = Field(title="Number of calls")
    average_success_time: Optional[int] = Field(
        title="Average fetch time in ms",
        description="How long it takes to fetch data "
        "(only takes successful calls into account)",
    )
    success_rate: Optional[float] = Field(title="Percentage of successful calls")
    timeout_rate: Optional[float] = Field(title="Percentage of calls that timed out")
    error_rate: Optional[float] = Field(title="Percentage of calls that failed")
    first_call: Optional[datetime]
    last_call: Optional[datetime]
