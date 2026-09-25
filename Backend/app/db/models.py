"""
app/db/models.py

Modèles SQLAlchemy représentant les tables existantes en base
(déjà importées depuis les CSV). Ces classes ne créent pas les
tables — elles reflètent un schéma déjà en place.
"""

from datetime import date, datetime

from sqlalchemy import (
    String,
    ForeignKey,
    Date,
    DateTime,
    Numeric,
    Boolean,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    employees: Mapped[list["Employee"]] = relationship(back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    professional_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.department_id"), nullable=False)
    job_title: Mapped[str] = mapped_column(String(150), nullable=False)
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("employees.employee_id"), nullable=True)
    employment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    employment_status: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="employees")
    manager: Mapped["Employee | None"] = relationship(remote_side=[employee_id])
    user: Mapped["User | None"] = relationship(back_populates="employee", uselist=False)
    leave_balances: Mapped[list["LeaveBalance"]] = relationship(back_populates="employee")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # "employee" | "hr_admin"
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="user")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    leave_balance_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(100), nullable=False)
    total_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    used_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    remaining_days: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    employee: Mapped["Employee"] = relationship(back_populates="leave_balances")