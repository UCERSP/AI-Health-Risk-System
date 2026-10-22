import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "health_records.db"
)


def get_connection():
    os.makedirs(
        os.path.dirname(DB_PATH),
        exist_ok=True
    )

    return sqlite3.connect(DB_PATH)


def init_database():

    with get_connection() as conn:

        # ---------------------------------------------
        # Users table
        # ---------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


        # ---------------------------------------------
        # Existing assessments table
        # ---------------------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                age INTEGER,
                bmi REAL,
                systolic INTEGER,
                diastolic INTEGER,
                glucose REAL,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
            )
        """)


        # ---------------------------------------------
        # Check whether user_id already exists
        # ---------------------------------------------

        columns = conn.execute(
            "PRAGMA table_info(assessments)"
        ).fetchall()

        column_names = [
            column[1]
            for column in columns
        ]


        # ---------------------------------------------
        # Add user_id to old database if needed
        # ---------------------------------------------

        if "user_id" not in column_names:

            conn.execute("""
                ALTER TABLE assessments
                ADD COLUMN user_id INTEGER
            """)


        conn.commit()


if __name__ == "__main__":

    init_database()

    print("========================================")
    print("DATABASE SETUP")
    print("========================================")

    print("Users table ready.")
    print("Assessments table ready.")
    print("user_id column checked.")
    print("Database setup completed successfully.")

    print("========================================")