import logging
from typing import Final, List, Optional, Union

from fastapi import APIRouter, HTTPException
from fastapi_utils.cbv import cbv
from pydantic import BaseModel
from starlette import status
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, FieldError, IntegrityError
from tortoise.query_utils import Q
from tortoise.queryset import QuerySet

from apixy import models
from apixy.config import SETTINGS
from apixy.entities.datasource import (
    DataSource,
    DataSourceInput,
    HTTPDataSource,
    MongoDBDataSource,
    SQLDataSource,
)

logger = logging.getLogger(__name__)

# settings this as a constant instead of an argument for the APIRouter constructor
# as that was duplicating the prefix (I suspect the @cbv decorator to be the cause)
PREFIX: Final[str] = "/datasources"

router = APIRouter(tags=["DataSources"])


class DataSourceUnion(BaseModel):
    __root__: Union[HTTPDataSource, MongoDBDataSource, SQLDataSource]


@cbv(router)
class DataSources:
    """Provides CRUD for data sources."""

    @staticmethod
    def get_datasource_url(datasource_id: int) -> str:
        """
        Resolve the API link for a data source.

        :param datasource_id: id of a DataSource object.
        :return: a string path
        """
        return router.url_path_for("get", datasource_id=str(datasource_id))

    @router.get(
        PREFIX + "/{datasource_id}",
        response_model=DataSourceUnion,
    )
    async def get(self, datasource_id: int) -> DataSourceUnion:
        """Endpoint for a single data source."""
        try:
            queryset = await models.DataSource.get(id=datasource_id)
            return DataSourceUnion.parse_obj(queryset.to_pydantic())
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err

    @router.get(
        PREFIX + "/",
        response_model=List[DataSourceUnion],
    )
    async def get_list(
        self, limit: int = SETTINGS.DEFAULT_PAGINATION_LIMIT, offset: int = 0
    ) -> List[DataSourceUnion]:
        """Endpoint for GET"""
        tmp = [
            p.to_pydantic()
            for p in await DataSourcesDB.get_paginated_datasources(limit, offset)
        ]
        print(tmp[0].json())
        return [DataSourceUnion.parse_obj(i) for i in tmp]

    @router.post(
        PREFIX + "/", status_code=status.HTTP_201_CREATED, response_class=Response
    )
    async def create(self, datasource_in: DataSourceInput) -> Response:
        """Creating a new data source"""
        datasource = await DataSourcesDB.save_datasource(datasource_in)
        return Response(
            status_code=status.HTTP_201_CREATED,
            headers={"Location": self.get_datasource_url(datasource)},
        )

    @router.put(
        PREFIX + "/{datasource_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def update(
        self, datasource_id: int, datasource_in: DataSourceInput
    ) -> Optional[Union[HTTPDataSource, SQLDataSource, MongoDBDataSource]]:
        """Updating an existing DataSource"""
        model = DataSourcesDB.datasource_for_update(datasource_id)
        if not await model.exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "DataSource with this ID does not exist."
            )
        await model.update(**datasource_in.dict(exclude={"id"}))
        return None

    @router.delete(
        PREFIX + "/{datasource_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def delete(self, datasource_id: int) -> Optional[Response]:
        """Deleting a DataSource"""
        queryset = DataSourcesDB.datasource_for_update(datasource_id)
        if not await queryset.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await queryset.delete()
        return None


class DataSourcesDB:
    async def url_exists(self, url: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a data source with passed url exists, excluding a specific ID.

        :param url: url to look for
        :param exclude_id: ID to exclude, if `None`, nothing will be excluded
        """
        return await models.DataSource.filter(Q(url=url) & ~Q(id=exclude_id)).exists()

    @staticmethod
    async def get_paginated_datasources(
        limit: int, offset: int
    ) -> List[models.DataSource]:
        """
        Fetch all data sources and apply limit-offset pagination.

        :param limit: how many to fetch
        :param offset: how many to skip
        :return: awaited queryset, so a list
        """
        return await models.DataSource.all().limit(limit).offset(offset)

    @staticmethod
    async def save_datasource(datasource: DataSource) -> int:
        """
        Try to save a data source to the DB.

        :param datasource: A DataSource entity
        :raise HTTPException: with status code 422
        :return: id of the record
        """
        model = models.DataSource.from_pydantic(datasource)
        try:
            await model.save()
            return model.id
        except (FieldError, IntegrityError) as err:
            logger.exception("DataSource save error.", extra={"exception": err})
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY) from err

    @staticmethod
    def datasource_for_update(datasource_id: int) -> QuerySet[models.DataSource]:
        """
        Select a data source by id, locking the DB row for the rest of the transaction.

        :param datasource_id: id to look for
        :return: a queryset filtered by id
        """
        return models.DataSource.filter(id=datasource_id).select_for_update()
