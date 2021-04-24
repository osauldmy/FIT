import logging
from typing import Final, List, Optional, Union

from fastapi import APIRouter, HTTPException
from fastapi_utils.cbv import cbv
from starlette import status
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist, FieldError, IntegrityError

from apixy import models
from apixy.entities.project import Project, ProjectBase, ProjectInput

logger = logging.getLogger(__name__)

# settings this as a constant instead of an argument for the APIRouter constructor
# as that was duplicating the prefix (I suspect the @cbv decorator to be the cause)
PREFIX: Final[str] = "/projects"

router = APIRouter(tags=["projects"])


@cbv(router)
class ProjectCBV:
    """Provides CRUD for Projects"""

    @staticmethod
    def get_project_link(project_id: int) -> str:
        """
        Resolve the API link for a Project.

        :param project_id: id of a project
        :return: a string path
        """
        return router.url_path_for("get", project_id=str(project_id))

    @staticmethod
    async def save_project(project: ProjectBase) -> int:
        """
        Try to save a Project to the DB.

        :param project: A Project entity, can be with or without an ID
        :raise HTTPException: with status code 422
        :return id of the record
        """
        model = models.Project(**project.dict())
        try:
            await model.save()
            return model.id
        except (FieldError, IntegrityError) as e:
            logger.error("Project save error.", extra={"exception": e})
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY) from e

    @router.get(PREFIX + "/{project_id}", response_model=Project)
    async def get(self, project_id: int) -> Union[Project, Response]:
        """Endpoint for a single project."""
        try:
            queryset = await models.Project.get(id=project_id)
            return queryset.to_pydantic()
        except DoesNotExist as e:
            raise HTTPException(status.HTTP_404_NOT_FOUND) from e

    @router.get(PREFIX + "/", response_model=List[Project])
    async def get_list(self, limit: int, offset: int) -> List[Project]:
        """Endpoint for GET"""
        return [
            p.to_pydantic()
            for p in await models.Project.all().limit(limit).offset(offset)
        ]

    @router.post(
        PREFIX + "/", status_code=status.HTTP_201_CREATED, response_class=Response
    )
    async def create(self, project_in: ProjectInput) -> Response:
        """Creating a new Project"""
        if await models.Project.filter(slug=project_in.slug).exists():
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Project with this slug already exists."
            )
        project_id = await self.save_project(project_in)
        return Response(
            status_code=status.HTTP_201_CREATED,
            headers={"Location": self.get_project_link(project_id)},
        )

    @router.put(
        PREFIX + "/{project_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def update(
        self, project_id: int, project_in: ProjectInput
    ) -> Optional[Response]:
        """Updating an existing Project"""
        if await models.Project.filter(slug=project_in.slug).exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Project with this slug already exists."
            )
        if not await models.Project.filter(id=project_id).select_for_update().exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Project with this ID does not exist."
            )
        await models.Project.filter(id=project_id).select_for_update().update(
            **project_in.dict()
        )
        return None

    @router.delete(
        PREFIX + "/{project_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
    )
    async def delete(self, project_id: int) -> Optional[Response]:
        """Deleting a Project"""
        queryset = models.Project.filter(id=project_id)
        if not await queryset.exists():
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await queryset.delete()
        return None
