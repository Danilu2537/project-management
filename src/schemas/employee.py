from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class EmployeeBase(BaseModel):
    name: str
    rank: Literal[1, 2, 3, 4]

    class Config:
        from_attributes = True


class EmployeeCreate(EmployeeBase):
    pass


class Employee(EmployeeBase):
    registered_at: datetime
    id: int


class EmployeeList(BaseModel):
    employees: list[Employee]
