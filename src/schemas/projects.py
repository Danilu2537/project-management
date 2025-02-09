from pydantic import BaseModel
from schemas.employee import Employee
from datetime import datetime


class ProjectBase(BaseModel):
    title: str
    description: str
    parent_project_id: int | None
    max_participants: int

    class Config:
        from_attributes = True


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectCreate):
    created_at: datetime
    id: int


class ProjectWithParticipants(Project):
    employees: list[Employee]


class ProjectWithChildren(ProjectWithParticipants):
    children: list["ProjectWithChildren"]


class ProjectList(BaseModel):
    projects: list[ProjectWithParticipants]
