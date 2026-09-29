import bcrypt
from sqlalchemy import create_engine, text
from app.config import DATABASE_URL

h = bcrypt.hashpw(b"Test1234!", bcrypt.gensalt()).decode()
e = create_engine(DATABASE_URL)
with e.begin() as c:
    c.execute(text("update users set password_hash = :h"), {"h": h})
print("ok")