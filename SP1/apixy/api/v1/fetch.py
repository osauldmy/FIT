from typing import Final, Optional

from fastapi import Depends, HTTPException, Query
from starlette import status
from tortoise.exceptions import DoesNotExist

from apixy.entities.proxy_response import ProxyResponse
from apixy.models import ProjectModel

from ...entities.project import FetchLogger
from .shared import ApixyRouter, get_fetch_logger

PREFIX_USER: Final[str] = "/collect"  # TODO: discuss possible prefixes

router = ApixyRouter(tags=["FetchRouter"])


@router.get(PREFIX_USER + "/{project_slug}", response_model=ProxyResponse)
async def fetch(
    project_slug: Optional[str] = Query(
        None, max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$"
    ),
    fetch_logger: FetchLogger = Depends(get_fetch_logger),
) -> ProxyResponse:
    """Fetches and aggregates all data sources tied to project slug."""
    try:
        model = await ProjectModel.get(slug=project_slug)
        project = await model.to_pydantic_with_datasources()
        return await project.fetch_data(fetch_logger)
    except DoesNotExist as err:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from err
