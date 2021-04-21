from typing import List

from fastapi import APIRouter
from fastapi_utils.cbv import cbv
from pydantic import UUID4
from starlette import status
from starlette.responses import Response

from apixy.entities.project import Project

router = APIRouter(tags=["projects"])


# todo implement the methods
@cbv(router)
class ProjectCBV:
    """Provides CRUD for Projects"""

    @router.get("/{project_id}")
    def get(self, project_id: UUID4) -> Project:
        """Endpoint for a single project."""

    @router.get("/")
    def get_list(self) -> List[Project]:
        """Endpoint for GET"""

    @router.post("/", status_code=status.HTTP_201_CREATED, response_class=Response)
    def create(self, project: Project) -> Response:
        """Creating a new Project"""
        # create project here, on success, return like
        # return Response(
        #     headers={"Location": "the-new-project-location"},
        # )

    @router.put(
        "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
    )
    def update(self, project: Project) -> Response:
        """Updating an existing Project"""

    @router.delete(
        "/{project_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
    )
    def delete(self, project_id: UUID4) -> Response:
        """Deleting a Project"""
