import logging
from typing import Final, List, Optional

from fastapi import APIRouter, HTTPException, Query
from starlette import status
from tortoise.exceptions import DoesNotExist

from apixy import models
from apixy.api.v1.datasources import DataSourceUnion

logger = logging.getLogger(__name__)

PREFIX_USER: Final[str] = "/collect"  # TODO: discuss possible prefixes

router = APIRouter(tags=["FetchRouter"])


# TODO: add appropriate data response model
@router.get(PREFIX_USER + "/{project_slug}", response_model=List[DataSourceUnion])
async def fetch(
    project_slug: Optional[str] = Query(
        None, max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$"
    ),
) -> List[DataSourceUnion]:
    """Fetches and aggregates all data sources tied to project slug."""
    try:
        model = await models.Project.get(slug=project_slug)
        project = await model.to_pydantic_with_datasources()
        # TODO: add fetching functionality
        return project.datasources
    except DoesNotExist as err:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from err
