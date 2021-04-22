from fastapi_crudrouter import TortoiseCRUDRouter

from apixy import models
from apixy.entities.project import Project, ProjectIn

router = TortoiseCRUDRouter(
    schema=Project,
    create_schema=ProjectIn,
    update_schema=ProjectIn,
    db_model=models.Project,
    prefix="projects",
    delete_all_route=False,
)
