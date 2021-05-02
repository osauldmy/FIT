import logging
from typing import Dict, Final, List, Optional, Union

from fastapi import Depends, HTTPException
from fastapi_utils.cbv import cbv
from starlette import status
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, FieldError, IntegrityError
from tortoise.query_utils import Q
from tortoise.queryset import QuerySet

from apixy.entities.project import Project, ProjectInput
from apixy.models import DataSourceModel, ProjectModel

from ...entities.proxy_response import ProxyResponse
from .datasources import DataSourceUnion
from .shared import ApixyRouter, pagination_params

logger = logging.getLogger(__name__)

# settings this as a constant instead of an argument for the APIRouter constructor
# as that was duplicating the prefix (I suspect the @cbv decorator to be the cause)
PREFIX: Final[str] = "/projects"
PROJECT_DATASOURCES_PREFIX: Final[str] = PREFIX + "/{project_id}/datasources"

router = ApixyRouter(tags=["Projects"])


async def get_project_by_id(project_id: int) -> ProjectModel:
    try:
        return await ProjectModel.get(id=project_id)
    except DoesNotExist as exception:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Invalid Project ID."
        ) from exception


@cbv(router)
class ProjectsView:
    """Provides CRUD for Projects"""

    @staticmethod
    def get_project_link(project_id: int) -> str:
        """
        Resolve the API link for a Project.

        :param project_id: id of a project
        :return: a string path
        """
        return router.url_path_for("get", project_id=str(project_id))

    @router.get(PREFIX + "/{project_id}", response_model=Project)
    async def get(
        self, project: ProjectModel = Depends(get_project_by_id)
    ) -> Union[Project, Response]:
        """Endpoint for a single project."""
        return project.to_pydantic()

    @router.get(PREFIX + "/", response_model=List[Project])
    async def get_list(
        self, pagination: Dict[str, int] = Depends(pagination_params)
    ) -> List[Project]:
        """Endpoint for GET"""
        return [
            p.to_pydantic()
            for p in await ProjectsDB.get_paginated_projects(
                pagination["limit"], pagination["offset"]
            )
        ]

    @router.post(PREFIX + "/")
    async def create(self, project_in: ProjectInput, response: Response) -> None:
        """Creating a new Project"""
        if await ProjectsDB.slug_exists(project_in.slug):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Project with this slug already exists."
            )
        project_id = await ProjectsDB.save_project(project_in)
        response.headers.update({"Location": self.get_project_link(project_id)})

    @router.put(PREFIX + "/{project_id}")
    async def update(
        self, project_id: int, project_in: ProjectInput
    ) -> Optional[Response]:
        """Updating an existing Project"""
        if await ProjectsDB.slug_exists(project_in.slug, project_id):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Project with this slug already exists."
            )
        model = ProjectsDB.project_for_update(project_id)
        if not await model.exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Project with this ID does not exist."
            )
        await model.update(**project_in.dict(exclude={"id"}))
        return None

    @router.delete(PREFIX + "/{project_id}")
    async def delete(self, project_id: int) -> Optional[Response]:
        """Deleting a Project"""
        queryset = ProjectsDB.project_for_update(project_id)
        if not await queryset.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await queryset.delete()
        return None

    @router.get(PREFIX + "/{project_id}/fetch", response_model=ProxyResponse)
    async def fetch(self, project_id: int) -> ProxyResponse:
        """Fetches and aggregates all data sources tied to project id."""
        try:
            model = await ProjectModel.get(id=project_id)
            project = await model.to_pydantic_with_datasources()
            return await project.fetch_data()
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err


@cbv(router)
class ProjectsDataSourcesView:
    project: ProjectModel = Depends(get_project_by_id)

    @router.put(PROJECT_DATASOURCES_PREFIX + "/{datasource_id}")
    async def add(self, datasource_id: int) -> None:
        """Adding an existing datasource to a project."""
        try:
            data_source = await DataSourceModel.get(id=datasource_id)
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err
        if data_source in await self.project.sources.all():
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Datasource already exists in this project",
            )
        await self.project.sources.add(data_source)

    @router.get(PROJECT_DATASOURCES_PREFIX, response_model=List[DataSourceUnion])
    async def list(
        self, project: ProjectModel = Depends(get_project_by_id)
    ) -> List[DataSourceUnion]:
        """List all data sources tied to a project id."""
        await project.fetch_related("sources")
        return [
            DataSourceUnion.parse_obj(i.to_pydantic()) for i in list(project.sources)
        ]

    @router.delete(PROJECT_DATASOURCES_PREFIX + "/{datasource_id}")
    async def remove(self, datasource_id: int) -> None:
        """Removing an existing datasource from a project."""
        datasource = [ds async for ds in self.project.sources if ds.id == datasource_id]
        if len(datasource) == 0:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No such datasource in this project"
            )
        await self.project.sources.remove(datasource[0])


class ProjectsDB:
    @staticmethod
    async def slug_exists(slug: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a project with passed slug exists, excluding a specific ID.

        :param slug: slug to look for
        :param exclude_id: ID to exclude, if `None`, nothing will be excluded
        """
        return await ProjectModel.filter(Q(slug=slug) & ~Q(id=exclude_id)).exists()

    @staticmethod
    async def get_paginated_projects(limit: int, offset: int) -> List[ProjectModel]:
        """
        Fetch all projects and apply limit-offset pagination.

        :param limit: how many to fetch
        :param offset: how many to skip
        :return: awaited queryset, so a list
        """
        return await ProjectModel.all().limit(limit).offset(offset)

    @staticmethod
    async def save_project(project: Project) -> int:
        """
        Try to save a Project to the DB.

        :param project: A Project entity, can be with or without an ID
        :raise HTTPException: with status code 422
        :return: id of the record
        """
        model = ProjectModel(**project.dict(exclude_unset=True))
        try:
            await model.save()
            return model.id
        except (FieldError, IntegrityError) as err:
            logger.exception("Project save error.", extra={"exception": err})
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY) from err

    @staticmethod
    def project_for_update(project_id: int) -> QuerySet[ProjectModel]:
        """
        Select a project by id, locking the DB row for the rest of the transaction.

        :param project_id: id to look for
        :return: a queryset filtered by id
        """
        return ProjectModel.filter(id=project_id).select_for_update()
