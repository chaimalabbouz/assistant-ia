from pydantic import BaseModel


class EmployeeProfile(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    professional_email: str
    phone: str | None = None
    department_id: str
    department_name: str
    job_title: str | None = None
    manager_id: str | None = None
    employment_type: str | None = None
    hire_date: str | None = None
    employment_status: str | None = None
    location: str | None = None


class DepartmentInfo(BaseModel):
    department_id: str
    department_name: str
    description: str | None = None


class ManagerInfo(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    professional_email: str
    job_title: str | None = None


class LeaveBalance(BaseModel):
    employee_id: str
    leave_type: str
    total_days: float
    used_days: float
    remaining_days: float
    year: int