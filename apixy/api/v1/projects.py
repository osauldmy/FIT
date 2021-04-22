from fastapi_crudrouter import TortoiseCRUDRouter

from apixy import models
from apixy.entities.project import Project, ProjectInput

router = TortoiseCRUDRouter(
    schema=Project,
    create_schema=ProjectInput,
    update_schema=ProjectInput,
    db_model=models.Project,
    prefix="projects",
    delete_all_route=False,
)
