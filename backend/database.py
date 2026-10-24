
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LOCAL_DB_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "data", "health_records.db")
)


class LocalCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        query = query.replace("%s", "?")

        if params is None:
            return self.cursor.execute(query)

        return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

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
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
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

    # Enforce foreign-key relationships in SQLite.
    connection.execute("PRAGMA foreign_keys = ON")

    return LocalConnection(connection)


def init_database():
    use_postgres = bool(os.environ.get("DATABASE_URL"))

    with get_connection() as conn:
        with conn.cursor() as cursor:

            # Create users table.
            if use_postgres:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            # Create assessments table.
            if use_postgres:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assessments (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        name TEXT NOT NULL,
                        age INTEGER,
                        bmi DOUBLE PRECISION,
                        systolic INTEGER,
                        diastolic INTEGER,
                        glucose DOUBLE PRECISION,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Add the date column to an existing table if needed.
                cursor.execute("""
                    ALTER TABLE assessments
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP
                """)

            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS assessments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER REFERENCES users(id),
                        name TEXT NOT NULL,
                        age INTEGER,
                        bmi REAL,
                        systolic INTEGER,
                        diastolic INTEGER,
                        glucose REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Check older SQLite databases for the date column.
                cursor.execute("PRAGMA table_info(assessments)")
                columns = [
                    row[1] for row in cursor.fetchall()
                ]

                if "created_at" not in columns:
                    cursor.execute("""
                        ALTER TABLE assessments
                        ADD COLUMN created_at TIMESTAMP
                    """)

    print("Database initialized successfully!")


if __name__ == "__main__":
    init_database()
    print("Database setup completed successfully.")
