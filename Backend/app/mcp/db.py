import psycopg2

from app.config import DATABASE_URL


def get_db_connection():
    # psycopg2 n'accepte pas le préfixe "+psycopg2" de SQLAlchemy
    dsn = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    return psycopg2.connect(dsn)