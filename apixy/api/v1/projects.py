from typing import List, Optional, Union

from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from pydantic import UUID4
from starlette import status
from starlette.responses import Response
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from apixy import models
from apixy.entities.project import Project, ProjectIn

router = APIRouter(tags=["projects"])


@cbv(router)
class ProjectCBV:
    """Provides CRUD for Projects"""

    @router.get("/{project_id}")
    async def get(self, project_id: UUID4) -> Union[Project, Response]:
        """Endpoint for a single project."""
        try:
            queryset = await models.Project.get(uuid=project_id)
            return queryset.to_pydantic()
        except DoesNotExist:
            return Response(status_code=status.HTTP_404_NOT_FOUND)

    @router.get("/")
    async def get_list(self) -> List[Project]:
        """Endpoint for GET"""
        return [p.to_pydantic() for p in await models.Project.all()]

    @router.post("/", status_code=status.HTTP_201_CREATED, response_class=Response)
    async def create(self, project_in: ProjectIn) -> Response:
        """Creating a new Project"""
        project = project_in.to_project()
        await models.Project.from_pydantic(project).save()
        return Response(
            headers={
                "Location": router.url_path_for("get", project_id=str(project.uuid))
            },
        )

    @router.put(
        "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
    )
    async def update(self, project: Project) -> Optional[Response]:
        """Updating an existing Project"""
        async with in_transaction():
            if not await models.Project.filter(uuid=project.uuid).exists():
                return Response(status_code=status.HTTP_404_NOT_FOUND)
            await models.Project.from_pydantic(project).save()
        return None

    @router.delete(
        "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
    )
    async def delete(self, project_id: UUID4) -> Optional[Response]:
        """Deleting a Project"""
        async with in_transaction():
            if not await models.Project.filter(uuid=project_id).exists():
                return Response(status_code=status.HTTP_404_NOT_FOUND)
            await models.Project.filter(uuid=project_id).delete()
        return None
