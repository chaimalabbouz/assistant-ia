from app.mcp.db import get_db_connection

from app.mcp.schemas.models import (
    EmployeeProfile,
    DepartmentInfo,
    ManagerInfo,
    LeaveBalance,
)


def get_employee_profile(employee_id: str) -> EmployeeProfile | None:

    query = """
        SELECT
            e.employee_id,
            e.first_name,
            e.last_name,
            e.professional_email,
            e.phone,
            e.department_id,
            d.department_name,
            e.job_title,
            e.manager_id,
            e.employment_type,
            e.hire_date,
            e.employment_status,
            e.location
        FROM employees e
        JOIN departments d
            ON e.department_id = d.department_id
        WHERE e.employee_id = %s;
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (employee_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return EmployeeProfile(
                employee_id=row[0],
                first_name=row[1],
                last_name=row[2],
                professional_email=row[3],
                phone=row[4],
                department_id=row[5],
                department_name=row[6],
                job_title=row[7],
                manager_id=row[8],
                employment_type=row[9],
                hire_date=str(row[10]) if row[10] else None,
                employment_status=row[11],
                location=row[12],
            )

    finally:
        connection.close()


def get_department_info(
    department_id: str,
) -> DepartmentInfo | None:

    query = """
        SELECT
            department_id,
            department_name,
            description
        FROM departments
        WHERE department_id = %s;
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (department_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return DepartmentInfo(
                department_id=row[0],
                department_name=row[1],
                description=row[2],
            )

    finally:
        connection.close()


def get_manager(
    employee_id: str,
) -> ManagerInfo | None:

    query = """
        SELECT
            m.employee_id,
            m.first_name,
            m.last_name,
            m.professional_email,
            m.job_title
        FROM employees e
        JOIN employees m
            ON e.manager_id = m.employee_id
        WHERE e.employee_id = %s;
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (employee_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return ManagerInfo(
                employee_id=row[0],
                first_name=row[1],
                last_name=row[2],
                professional_email=row[3],
                job_title=row[4],
            )

    finally:
        connection.close()


def get_leave_balance(
    employee_id: str,
) -> list[LeaveBalance]:

    query = """
        SELECT
            employee_id,
            leave_type,
            total_days,
            used_days,
            remaining_days,
            year
        FROM leave_balances
        WHERE employee_id = %s
        ORDER BY year DESC, leave_type;
    """

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (employee_id,))
            rows = cursor.fetchall()

            return [
                LeaveBalance(
                    employee_id=row[0],
                    leave_type=row[1],
                    total_days=float(row[2]),
                    used_days=float(row[3]),
                    remaining_days=float(row[4]),
                    year=row[5],
                )
                for row in rows
            ]

    finally:
        connection.close()