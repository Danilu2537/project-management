from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Response
from dependencies import get_db
from schemas.projects import (
    ProjectList,
    ProjectWithParticipants,
    ProjectCreate,
    ProjectWithChildren,
)
from models import Project, Employee, projects_participants
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from services.utils import add_employee_to_project
from sqlalchemy.orm import joinedload


async def update_project(id: int, project: ProjectCreate, db: AsyncSession = Depends(get_db)):
    async with db:
        db_project = (await db.execute(select(Project).filter(Project.id == id))).scalars().first()
        db_project.title = project.title
        db_project.description = project.description
        db_project.max_participants = project.max_participants
        db_project.parent_project_id = project.parent_project_id
        await db.commit()
        await db.refresh(db_project)
        return db_project


async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    async with db:
        db_project = Project(**project.model_dump())
        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)
        return db_project


async def delete_project(id: int, db: AsyncSession = Depends(get_db)):
    """Удаление проекта с вложенными проектами."""
    async with db:
        # Удаляем проект
        project = (
            (await db.execute(select(Project).filter(Project.id == id).options(joinedload(Project.children))))
            .scalars()
            .first()
        )
        # Удаляем записи сотрудников-участников
        await db.execute(delete(projects_participants).where(projects_participants.c.project_id == id))
        # Удаляем вложенные проекты
        for child in project.children:
            await delete_project(child.id, db)
        project.is_deleted = True
        db.add(project)
        await db.commit()
        return Response(status_code=204)


async def get_top_projects(db: AsyncSession = Depends(get_db)) -> ProjectList:
    async with db:
        result = await db.execute(
            select(Project).filter(Project.is_deleted == False)  # noqa E712
        )
        return ProjectList(projects=result.scalars().all())


async def get_projects(
    db: AsyncSession = Depends(get_db),
    with_participants: bool = True,
    search: str = None,
) -> ProjectList:
    async with db:
        query = select(Project).filter(Project.is_deleted == False)  # noqa E712

        if with_participants:
            query = query.options(selectinload(Project.employees))

        if search:
            query = query.where(Project.title.contains(search))

        result = await db.execute(query.order_by(Project.created_at.desc()))
        projects = result.scalars().all()
        return ProjectList(projects=projects)


async def get_project_with_children(id: int, db: AsyncSession = Depends(get_db)) -> ProjectWithChildren:
    async with db:
        # Рекурсивно получаем все ID проектов в иерархии
        cte = select(Project.id).where(Project.id == id).cte(name="project_tree", recursive=True)

        children = select(Project.id).where(Project.parent_project_id == cte.c.id)
        cte = cte.union_all(children)

        project_ids = await db.execute(select(cte.c.id))
        project_ids = [row.id for row in project_ids]

        # Загружаем все проекты с сотрудниками
        projects = await db.execute(
            select(Project)
            .options(selectinload(Project.employees), selectinload(Project.children))
            .where(Project.id.in_(project_ids))
            .where(Project.is_deleted == False)  # noqa E712
        )
        projects = projects.scalars().all()

        projects_by_id = {p.id: p for p in projects}
        for project in projects:
            project.children = [p for p in projects if p.parent_project_id == project.id]

        def convert(project: Project) -> ProjectWithChildren:
            project_data = ProjectWithParticipants(**project.__dict__)
            return ProjectWithChildren(
                **project_data.model_dump(),
                children=[convert(child) for child in project.children],
            )

        return convert(projects_by_id[id])


async def add_participant(
    project_id: int,
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    force: bool = False,
):
    async with db:
        project = await add_employee_to_project(db, project_id, employee_id, force)
        return ProjectWithParticipants(**project.__dict__)


async def delete_participant(project_id: int, employee_id: int, db: AsyncSession = Depends(get_db)):
    async with db:
        project = (await db.execute(select(Project).filter(Project.id == project_id))).scalars().first()
        employee = (await db.execute(select(Employee).filter(Employee.id == employee_id))).scalars().first()
        try:
            project.employees.remove(employee)
            await db.commit()
        except ValueError:
            pass
        return Response(status_code=204)
