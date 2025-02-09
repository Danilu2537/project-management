from fastapi import Depends
from fastapi.responses import Response
from dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models import Employee
from schemas.employee import EmployeeCreate, EmployeeList
from sqlalchemy import select


async def create_employee(employee: EmployeeCreate, db: AsyncSession = Depends(get_db)) -> Employee:
    async with db:
        db_employee = Employee(**employee.model_dump())
        db.add(db_employee)
        await db.commit()
        await db.refresh(db_employee)
        return db_employee


async def update_employee(id: int, employee: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    async with db:
        db_employee = (await db.execute(select(Employee).filter(Employee.id == id))).scalars().first()
        db_employee.name = employee.name
        db_employee.rank = employee.rank
        await db.commit()
        await db.refresh(db_employee)
        return db_employee


async def delete_employee(id: int, db: AsyncSession = Depends(get_db)):
    async with db:
        employee = await db.get(Employee, id)
        employee.is_deleted = True
        await db.commit()
        return Response(status_code=204)


async def get_employees(db: AsyncSession = Depends(get_db)) -> EmployeeList:
    async with db:
        result = await db.execute(
            select(Employee).filter(Employee.is_deleted == False)  # noqa E712
        )
        return EmployeeList(employees=result.scalars().all())
