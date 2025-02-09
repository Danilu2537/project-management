from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Column, Integer, Table, CheckConstraint
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    parent_project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    max_participants: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    parent: Mapped["Project"] = relationship("Project", remote_side=[id])
    children: Mapped[list["Project"]] = relationship(
        "Project", back_populates="parent", remote_side=[parent_project_id]
    )
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        secondary="projects_participants",
        back_populates="projects",
        lazy="selectin",
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    rank: Mapped[int] = mapped_column(CheckConstraint("rank in (1, 2, 3, 4)"))
    registered_at: Mapped[datetime] = mapped_column(default=datetime.now)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    projects: Mapped[list["Project"]] = relationship(
        "Project", secondary="projects_participants", back_populates="employees"
    )


projects_participants = Table(
    "projects_participants",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id")),
    Column("participant_id", Integer, ForeignKey("employees.id")),
)
