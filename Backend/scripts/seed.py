"""
scripts/seed.py

Crée les tables sur la base pointée par DATABASE_URL (Neon) et charge les CSV.
Usage (depuis le dossier Backend) :
    python -m scripts.seed            # refuse de tourner si des données existent
    python -m scripts.seed --reset    # supprime tout et recharge
"""

import csv
import sys
from datetime import date, datetime

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.config import DATABASE_URL, DATA_DIR
from app.db.models import Base, Department, Employee, LeaveBalance, User

SEED_DIR = DATA_DIR / "seed"


def read_csv(name: str) -> list[dict]:
    with open(SEED_DIR / f"{name}.csv", "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    # chaîne vide -> None
    return [{k: (v if v != "" else None) for k, v in row.items()} for row in rows]


def main():
    reset = "--reset" in sys.argv
    engine = create_engine(DATABASE_URL)
    host = engine.url.host
    print(f"Base cible : {host}")

    if reset:
        print("Suppression des tables existantes...")
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        if session.scalar(select(func.count()).select_from(Department)) > 0:
            print("Des données existent déjà. Relance avec --reset pour tout recharger.")
            return

        # 1. Départements
        for r in read_csv("departments"):
            session.add(Department(**r))
        session.flush()

        # 2. Employés (manager_id mis à NULL d'abord, car auto-référence)
        managers = {}
        for r in read_csv("employees"):
            managers[r["employee_id"]] = r.pop("manager_id")
            r["hire_date"] = date.fromisoformat(r["hire_date"])
            session.add(Employee(**r, manager_id=None))
        session.flush()

        for emp_id, mgr_id in managers.items():
            if mgr_id:
                session.get(Employee, emp_id).manager_id = mgr_id
        session.flush()

        # 3. Soldes de congés
        for r in read_csv("leave_balances"):
            r["total_days"] = float(r["total_days"])
            r["used_days"] = float(r["used_days"])
            r["remaining_days"] = float(r["remaining_days"])
            r["year"] = int(r["year"])
            r["updated_at"] = datetime.fromisoformat(r["updated_at"])
            session.add(LeaveBalance(**r))

        # 4. Utilisateurs
        for r in read_csv("users"):
            r["is_active"] = r["is_active"].strip().lower() == "true"
            r["last_login"] = datetime.fromisoformat(r["last_login"]) if r["last_login"] else None
            r["created_at"] = datetime.fromisoformat(r["created_at"])
            session.add(User(**r))

        session.commit()

        for model in (Department, Employee, LeaveBalance, User):
            n = session.scalar(select(func.count()).select_from(model))
            print(f"{model.__tablename__} : {n} lignes")

    print("Seed terminé.")


if __name__ == "__main__":
    main()