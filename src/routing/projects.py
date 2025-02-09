from fastapi import APIRouter
from services.project import (
    get_projects,
    add_participant,
    delete_participant,
    delete_project,
    get_project_with_children,
    get_top_projects,
    create_project,
    update_project,
)
from schemas.projects import (
    ProjectList,
    ProjectWithParticipants,
    Project,
    ProjectWithChildren,
)

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

router.add_api_route("/", get_projects, methods=["GET"], response_model=ProjectList)
router.add_api_route("/", create_project, methods=["POST"], response_model=Project)
router.add_api_route(
    "/{id}/",
    get_project_with_children,
    methods=["GET"],
    response_model=ProjectWithChildren,
)
router.add_api_route("/{id}/", update_project, methods=["PUT"], response_model=Project)
router.add_api_route("/{id}/", delete_project, methods=["DELETE"])
router.add_api_route("/top/", get_top_projects, methods=["GET"], response_model=ProjectList)
router.add_api_route(
    "/{project_id}/participants/{employee_id}/",
    add_participant,
    methods=["POST"],
    response_model=ProjectWithParticipants,
)
router.add_api_route(
    "/{project_id}/participants/{employee_id}/",
    delete_participant,
    methods=["DELETE"],
    response_model=ProjectWithParticipants,
)
