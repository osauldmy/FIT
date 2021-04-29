import logging
from typing import Final, List, Optional, Union

from fastapi import APIRouter, HTTPException
from fastapi_utils.cbv import cbv
from starlette import status
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, FieldError, IntegrityError
from tortoise.query_utils import Q
from tortoise.queryset import QuerySet

from apixy import models
from apixy.api.v1.datasources import DataSourceUnion
from apixy.config import SETTINGS
from apixy.entities.project import Project, ProjectInput

logger = logging.getLogger(__name__)

# settings this as a constant instead of an argument for the APIRouter constructor
# as that was duplicating the prefix (I suspect the @cbv decorator to be the cause)
PREFIX: Final[str] = "/projects"

router = APIRouter(tags=["Projects"])


@cbv(router)
class Projects:
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
    async def get(self, project_id: int) -> Union[Project, Response]:
        """Endpoint for a single project."""
        try:
            queryset = await models.Project.get(id=project_id)
            return queryset.to_pydantic()
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err

    @router.get(PREFIX + "/", response_model=List[Project])
    async def get_list(
        self, limit: int = SETTINGS.DEFAULT_PAGINATION_LIMIT, offset: int = 0
    ) -> List[Project]:
        """Endpoint for GET"""
        return [
            p.to_pydantic()
            for p in await ProjectsDB.get_paginated_projects(limit, offset)
        ]

    @router.post(
        PREFIX + "/", status_code=status.HTTP_201_CREATED, response_class=Response
    )
    async def create(self, project_in: ProjectInput) -> Response:
        """Creating a new Project"""
        if await ProjectsDB.slug_exists(project_in.slug):
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Project with this slug already exists."
            )
        project_id = await ProjectsDB.save_project(project_in)
        return Response(
            status_code=status.HTTP_201_CREATED,
            headers={"Location": self.get_project_link(project_id)},
        )

    @router.post(
        PREFIX + "/{project_id}/add",
        status_code=status.HTTP_201_CREATED,
        response_class=Response,
    )
    async def add(self, project_id: int, datasource_id: int) -> Response:
        """Adding an existing datasource to a project."""
        try:
            project = await models.Project.get(id=project_id)
            data_source = await models.DataSource.get(id=datasource_id)
            await project.sources.add(data_source)
            return Response(
                status_code=status.HTTP_201_CREATED,
                headers={
                    "Location": self.get_project_link(project_id),
                },
            )
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err

    @router.get(
        PREFIX + "/{project_id}/datasources", response_model=List[DataSourceUnion]
    )
    async def list(self, project_id: int) -> List[DataSourceUnion]:
        """List all data sources tied to a project id."""
        try:
            project = await models.Project.get(id=project_id)
            await project.fetch_related("sources")
            return [
                DataSourceUnion.parse_obj(i.to_pydantic())
                for i in list(project.sources)
            ]
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err

    @router.delete(
        PREFIX + "/{project_id}/remove",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def remove(self, project_id: int, datasource_id: int) -> Response:
        """Removing an existing datasource from a project."""
        try:
            project = await models.Project.get(id=project_id)
            data_source = await models.DataSource.get(id=datasource_id)
            await project.sources.remove(data_source)
            return Response(
                status_code=status.HTTP_204_NO_CONTENT,
                headers={
                    "Location": self.get_project_link(project_id),
                },
            )
        except DoesNotExist as err:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from err

    @router.put(
        PREFIX + "/{project_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
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

    @router.delete(
        PREFIX + "/{project_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def delete(self, project_id: int) -> Optional[Response]:
        """Deleting a Project"""
        queryset = ProjectsDB.project_for_update(project_id)
        if not await queryset.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await queryset.delete()
        return None


class ProjectsDB:
    @staticmethod
    async def slug_exists(slug: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a project with passed slug exists, excluding a specific ID.

        :param slug: slug to look for
        :param exclude_id: ID to exclude, if `None`, nothing will be excluded
        """
        return await models.Project.filter(Q(slug=slug) & ~Q(id=exclude_id)).exists()

    @staticmethod
    async def get_paginated_projects(limit: int, offset: int) -> List[models.Project]:
        """
        Fetch all projects and apply limit-offset pagination.

        :param limit: how many to fetch
        :param offset: how many to skip
        :return: awaited queryset, so a list
        """
        return await models.Project.all().limit(limit).offset(offset)

    @staticmethod
    async def save_project(project: Project) -> int:
        """
        Try to save a Project to the DB.

        :param project: A Project entity, can be with or without an ID
        :raise HTTPException: with status code 422
        :return: id of the record
        """
        model = models.Project(**project.dict(exclude_unset=True))
        try:
            await model.save()
            return model.id
        except (FieldError, IntegrityError) as err:
            logger.exception("Project save error.", extra={"exception": err})
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY) from err

    @staticmethod
    def project_for_update(project_id: int) -> QuerySet[models.Project]:
        """
        Select a project by id, locking the DB row for the rest of the transaction.

        :param project_id: id to look for
        :return: a queryset filtered by id
        """
        return models.Project.filter(id=project_id).select_for_update()
