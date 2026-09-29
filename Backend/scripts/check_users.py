from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

e = create_engine(DATABASE_URL)
with e.connect() as c:
    rows = c.execute(
        text("select email, role, is_active, length(password_hash) from users limit 3")
    ).fetchall()
    for r in rows:
        print(r)