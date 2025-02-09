from sqlalchemy.ext.asyncio import AsyncSession
from models import Project, Employee, projects_participants
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import aliased, joinedload
from fastapi.exceptions import HTTPException


async def get_project(db: AsyncSession, project_id: int) -> Project | None:
    return (
        (
            await db.execute(
                select(Project)
                .filter(Project.id == project_id)  # noqa E712
                .options(joinedload(Project.employees))
            )
        )
        .scalars()
        .first()
    )


async def get_employee(db: AsyncSession, employee_id: int) -> Employee | None:
    return (
        (await db.execute(select(Employee).filter(Employee.id == employee_id).options(joinedload(Employee.projects))))
        .scalars()
        .first()
    )


async def get_top_level_project(db: AsyncSession, project_id: int):
    """Находит верхнеуровневый проект с использованием SQLAlchemy CTE."""

    pr = aliased(Project)

    project_cte = (
        select(Project.id, Project.parent_project_id)
        .where(Project.id == project_id)
        .cte(name="project_hierarchy", recursive=True)
    )

    # Рекурсивное объединение
    project_cte = project_cte.union_all(
        select(pr.id, pr.parent_project_id).join(project_cte, pr.id == project_cte.c.parent_project_id)
    )

    # Выбираем верхний уровень (где parent_project_id IS NULL)
    query = select(Project).where(
        Project.id == select(project_cte.c.id).where(project_cte.c.parent_project_id.is_(None)).limit(1)
    )

    return (await db.execute(query)).scalars().first()


async def count_top_level_assignments(db: AsyncSession, employee: Employee) -> int:
    """Подсчитывает количество верхнеуровневых проектов, в которых участвует сотрудник."""
    return len(
        (
            await db.execute(
                select(Project)
                .join(Project.employees)
                .filter(Employee.id == employee.id, Project.parent_project_id == None)  # noqa E712
            )
        )
        .scalars()
        .all()
    )


async def count_subproject_assignments(db: AsyncSession, employee_id: int, top_level_project_id: int) -> int:
    """Подсчитывает количество подпроектов внутри указанного верхнеуровневого проекта."""

    # Алиас для рекурсивного CTE
    ph = aliased(Project)

    # Рекурсивное CTE для поиска всех проектов, вложенных в top_level_project_id
    project_cte = (
        select(Project.id, Project.parent_project_id)
        .where(Project.id == top_level_project_id)
        .cte(name="project_hierarchy", recursive=True)
    )

    # Рекурсивное объединение (ищем все вложенные проекты)
    project_cte = project_cte.union_all(
        select(ph.id, ph.parent_project_id).join(project_cte, ph.parent_project_id == project_cte.c.id)
    )

    # Считаем, сколько раз сотрудник участвует в этих подпроектах
    query = select(func.count())
    query = query.select_from(Project).join(project_cte, Project.id == project_cte.c.id)
    query = query.join(projects_participants, Project.id == projects_participants.c.project_id)
    query = query.where(projects_participants.c.participant_id == employee_id)

    result = await db.execute(query)
    return result.scalar() or 0


async def add_employee_to_project(db: AsyncSession, project_id: int, employee_id: int, force: bool = False):
    """
    Добавляет сотрудника в проект с проверкой бизнес-правил.

    Параметр force позволяет пользователю сервиса принять решение о конфликте (например,
    игнорировать ограничение). По умолчанию при нарушении ограничений выбрасывается HTTPException.
    """
    employee = await get_employee(db, employee_id)
    project = await get_project(db, project_id)
    if not employee or not project:
        raise HTTPException(status_code=404, detail="Employee or Project not found")

    # Проверка на превышение максимального количества участников в проекте
    if len(project.employees) >= project.max_participants:
        raise HTTPException(status_code=400, detail="Project reached maximum participants")

    # Если сотрудник уже добавлен — ошибка
    if employee in project.employees:
        raise HTTPException(status_code=400, detail="Employee already assigned to this project")

    # Сотрудники 1-го ранга не ограничены
    if employee.rank != 1:
        if project.parent_project_id is None:
            # Добавление в верхнеуровневый проект
            top_level_count = await count_top_level_assignments(db, employee)
            if employee.rank == 2 and top_level_count >= 3:
                if not force:
                    raise HTTPException(
                        status_code=400,
                        detail="Rank 2 employee cannot be in more than 3 top-level projects",
                    )
            elif employee.rank == 3 and top_level_count >= 2:
                if not force:
                    raise HTTPException(
                        status_code=400,
                        detail="Rank 3 employee cannot be in more than 2 top-level projects",
                    )
            elif employee.rank == 4 and top_level_count >= 1:
                if not force:
                    raise HTTPException(
                        status_code=400,
                        detail="Rank 4 employee cannot be in more than 1 top-level project",
                    )
        else:
            # Добавление в подпроект
            top_project = await get_top_level_project(db, project.id)
            # Для подпроекта сотрудник должен уже состоять в соответствующем верхнеуровневом проекте
            if top_project not in employee.projects:
                if not force:
                    raise HTTPException(
                        status_code=400,
                        detail="Employee must be assigned to the top-level project before being added to its subproject",
                    )
            else:
                sub_count = await count_subproject_assignments(db, employee.id, top_project.id)
                if employee.rank == 3 and sub_count >= 2:
                    if not force:
                        raise HTTPException(
                            status_code=400,
                            detail="Rank 3 employee cannot be in more than 2 subprojects within a top-level project",
                        )
                elif employee.rank == 4 and sub_count >= 1:
                    if not force:
                        raise HTTPException(
                            status_code=400,
                            detail="Rank 4 employee cannot be in more than 1 subproject within a top-level project",
                        )

    # Если все проверки пройдены, добавляем сотрудника в проект
    project.employees.append(employee)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project
