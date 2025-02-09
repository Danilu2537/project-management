from fastapi import APIRouter
from services.employee import (
    create_employee,
    get_employees,
    delete_employee,
    update_employee,
)
from schemas.employee import Employee, EmployeeList

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
)

router.add_api_route("/", create_employee, methods=["POST"], response_model=Employee)
router.add_api_route("/{id}/", update_employee, methods=["PUT"], response_model=Employee)
router.add_api_route("/", get_employees, methods=["GET"], response_model=EmployeeList)
router.add_api_route("/{id}/", delete_employee, methods=["DELETE"])
