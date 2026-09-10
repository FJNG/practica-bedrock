import sqlite3
from pathlib import Path


DB_PATH = Path("data/app.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            prompt TEXT NOT NULL,
            style TEXT NOT NULL,
            seed INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


def create_user(name: str, role: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, role)
        VALUES (?, ?)
        """,
        (name, role)
    )

    connection.commit()
    connection.close()


def get_users():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, role
        FROM users
        ORDER BY name
    """)

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "role": row[2]
        }
        for row in rows
    ]


def create_project(name: str, created_by: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (name, created_by)
        VALUES (?, ?)
        """,
        (name, created_by)
    )

    connection.commit()
    connection.close()


def get_projects():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, created_by
        FROM projects
        ORDER BY name
    """)

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "created_by": row[2]
        }
        for row in rows
    ]

def save_image_record(
    project_id: int,
    user_id: int,
    filename: str,
    prompt: str,
    style: str,
    seed: int,
    created_at: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO images (
            project_id,
            user_id,
            filename,
            prompt,
            style,
            seed,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            user_id,
            filename,
            prompt,
            style,
            seed,
            created_at
        )
    )

    connection.commit()
    connection.close()


def get_images():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            project_id,
            user_id,
            filename,
            prompt,
            style,
            seed,
            created_at
        FROM images
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "project_id": row[1],
            "user_id": row[2],
            "filename": row[3],
            "prompt": row[4],
            "style": row[5],
            "seed": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]

def delete_image_by_filename(filename: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM images WHERE filename = ?",
        (filename,)
    )

    connection.commit()
    connection.close()