import logging
from typing import Dict, Final, List, Optional, Union

from fastapi import Depends, HTTPException
from fastapi_utils.cbv import cbv
from starlette import status
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, FieldError, IntegrityError
from tortoise.query_utils import Q
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction

from apixy.entities.datasource import (
    DataSource,
    DataSourceInput,
    DataSourceUnion,
    HTTPDataSource,
    MongoDBDataSource,
    SQLDataSource,
)
from apixy.models import DataSourceModel

from .shared import ApixyRouter, pagination_params

logger = logging.getLogger(__name__)

# settings this as a constant instead of an argument for the APIRouter constructor
# as that was duplicating the prefix (I suspect the @cbv decorator to be the cause)
PREFIX: Final[str] = "/datasources"

router = ApixyRouter(tags=["DataSources"])


@cbv(router)
class DataSourcesView:
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
            queryset = await DataSourceModel.get(id=datasource_id)
            return DataSourceUnion.parse_obj(queryset.to_pydantic())
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err

    @router.get(
        PREFIX + "/",
        response_model=List[DataSourceUnion],
    )
    async def get_list(
        self, pagination: Dict[str, int] = Depends(pagination_params)
    ) -> List[DataSourceUnion]:
        """Endpoint for GET"""
        return [
            DataSourceUnion.parse_obj(p.to_pydantic())
            for p in await DataSourcesDB.get_paginated_datasources(
                pagination["limit"], pagination["offset"]
            )
        ]

    @router.post(PREFIX + "/")
    async def create(self, datasource_in: DataSourceInput) -> Response:
        """Creating a new data source"""
        datasource = await DataSourcesDB.save_datasource(datasource_in)
        return Response(
            status_code=status.HTTP_201_CREATED,
            headers={"Location": self.get_datasource_url(datasource)},
        )

    @router.put(PREFIX + "/{datasource_id}")
    async def update(
        self, datasource_id: int, datasource_in: DataSourceInput
    ) -> Optional[Union[HTTPDataSource, SQLDataSource, MongoDBDataSource]]:
        """Updating an existing DataSource"""
        async with in_transaction():
            model = await DataSourcesDB.datasource_for_update(datasource_id).first()
            if model is None:
                raise HTTPException(
                    status.HTTP_404_NOT_FOUND, "DataSource with this ID does not exist."
                )
            if model.type != datasource_in.type:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "Cannot change datasource type.",
                )
            model.apply_update(datasource_in)
            await model.save()
        return None

    @router.delete(PREFIX + "/{datasource_id}")
    async def delete(self, datasource_id: int) -> Optional[Response]:
        """Deleting a DataSource"""
        queryset = DataSourcesDB.datasource_for_update(datasource_id)
        if not await queryset.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await queryset.delete()
        return None


class DataSourcesDB:
    @staticmethod
    async def url_exists(url: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a data source with passed url exists, excluding a specific ID.

        :param url: url to look for
        :param exclude_id: ID to exclude, if `None`, nothing will be excluded
        """
        return await DataSourceModel.filter(Q(url=url) & ~Q(id=exclude_id)).exists()

    @staticmethod
    async def get_paginated_datasources(
        limit: int, offset: int
    ) -> List[DataSourceModel]:
        """
        Fetch all data sources and apply limit-offset pagination.

        :param limit: how many to fetch
        :param offset: how many to skip
        :return: awaited queryset, so a list
        """
        return await DataSourceModel.all().limit(limit).offset(offset)

    @staticmethod
    async def save_datasource(datasource: DataSource) -> int:
        """
        Try to save a data source to the DB.

        :param datasource: A DataSource entity
        :raise HTTPException: with status code 422
        :return: id of the record
        """
        model = DataSourceModel.from_pydantic(datasource)
        try:
            await model.save()
            return model.id
        except (FieldError, IntegrityError) as err:
            logger.exception("DataSource save error.", extra={"exception": err})
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY) from err

    @staticmethod
    def datasource_for_update(datasource_id: int) -> QuerySet[DataSourceModel]:
        """
        Select a data source by id, locking the DB row for the rest of the transaction.

        :param datasource_id: id to look for
        :return: a queryset filtered by id
        """
        return DataSourceModel.filter(id=datasource_id).select_for_update()
