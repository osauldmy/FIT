from typing import Final, Optional

from fastapi import APIRouter, HTTPException, Query
from starlette import status
from tortoise.exceptions import DoesNotExist

from apixy import models
from apixy.entities.proxy_response import ProxyResponse

PREFIX_USER: Final[str] = "/collect"  # TODO: discuss possible prefixes

router = APIRouter(tags=["FetchRouter"])


@router.get(PREFIX_USER + "/{project_slug}", response_model=ProxyResponse)
async def fetch(
    project_slug: Optional[str] = Query(
        None, max_length=64, regex="^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$"
    )
) -> ProxyResponse:
    """Fetches and aggregates all data sources tied to project slug."""
    try:
        model = await models.ProjectModel.get(slug=project_slug)
        project = await model.to_pydantic_with_datasources()
        return await project.fetch_data()
    except DoesNotExist as err:
        raise HTTPException(status.HTTP_404_NOT_FOUND) from err
