"""
app/mcp/services/ticket_service.py

Service de création et lecture des tickets RH.
Même pattern que employee_service.py : accès DB direct via psycopg2,
pas de logique d'identité ici (employee_id est déjà résolu en amont).
"""

import uuid
from datetime import datetime, timezone

from app.mcp.db import get_db_connection
from app.mcp.schemas.models import TicketInfo

VALID_CATEGORIES = {"legal", "harassment", "salary", "personal_data", "other"}


def create_ticket(employee_id: str, question: str, category: str) -> TicketInfo:
    """
    Crée un nouveau ticket RH en base, avec le statut initial "pending".
    """
    if category not in VALID_CATEGORIES:
        category = "other"

    ticket_id = f"TKT{uuid.uuid4().hex[:10].upper()}"
    created_at = datetime.now(timezone.utc)

    query = """
        INSERT INTO tickets (ticket_id, employee_id, question, category, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s);
    """

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (ticket_id, employee_id, question, category, "pending", created_at),
            )
        connection.commit()
    finally:
        connection.close()

    return TicketInfo(
        ticket_id=ticket_id,
        employee_id=employee_id,
        question=question,
        category=category,
        status="pending",
        created_at=str(created_at),
    )


def get_tickets_for_employee(employee_id: str) -> list[TicketInfo]:
    """
    Retourne tous les tickets créés par un employé donné.
    """
    query = """
        SELECT ticket_id, employee_id, question, category, status, created_at
        FROM tickets
        WHERE employee_id = %s
        ORDER BY created_at DESC;
    """

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (employee_id,))
            rows = cursor.fetchall()

            return [
                TicketInfo(
                    ticket_id=row[0],
                    employee_id=row[1],
                    question=row[2],
                    category=row[3],
                    status=row[4],
                    created_at=str(row[5]),
                )
                for row in rows
            ]
    finally:
        connection.close()


def get_all_tickets() -> list[TicketInfo]:
    """
    Retourne tous les tickets, tous employés confondus (usage RH admin).
    """
    query = """
        SELECT ticket_id, employee_id, question, category, status, created_at
        FROM tickets
        ORDER BY created_at DESC;
    """

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

            return [
                TicketInfo(
                    ticket_id=row[0],
                    employee_id=row[1],
                    question=row[2],
                    category=row[3],
                    status=row[4],
                    created_at=str(row[5]),
                )
                for row in rows
            ]
    finally:
        connection.close()