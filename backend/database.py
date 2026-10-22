
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DB_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "data", "health_records.db")
)


class LocalCursor:
    """Allows existing %s queries to work with local SQLite."""

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("%s", "?")
        if params is None:
            return self.cursor.execute(query)
        return self.cursor.execute(query, params)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()


class LocalConnection:
    def __init__(self, connection):
        self.connection = connection

    def cursor(self):
        return LocalCursor(self.connection.cursor())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()


def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor
        )

    os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
    connection = sqlite3.connect(LOCAL_DB_PATH)
    return LocalConnection(connection)


def init_database():
    if os.environ.get("DATABASE_URL"):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assessments (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        name TEXT NOT NULL,
                        age INTEGER,
                        bmi DOUBLE PRECISION,
                        systolic INTEGER,
                        diastolic INTEGER,
                        glucose DOUBLE PRECISION
                    )
                """)

                cursor.execute("""
                    ALTER TABLE assessments
                    ADD COLUMN IF NOT EXISTS user_id INTEGER
                    REFERENCES users(id)
                """)
        print("PostgreSQL database initialized successfully!")

    else:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER REFERENCES users(id),
                        name TEXT NOT NULL,
                        age INTEGER,
                        bmi REAL,
                        systolic INTEGER,
                        diastolic INTEGER,
                        glucose REAL
                    )
                """)
        print("Local SQLite database initialized successfully!")


if __name__ == "__main__":
    init_database()
    print("Database setup completed successfully.")
