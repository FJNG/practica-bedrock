import sqlite3
from pathlib import Path
import json


DB_PATH = Path("data/app.db")


import sqlite3


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    # =========================================================
    # USUARIOS
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL
        )
    """)

    # =========================================================
    # PROYECTOS
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # =========================================================
    # CONTENIDO TEXTUAL
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS text_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS text_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            text TEXT NOT NULL,
            action TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (content_id) REFERENCES text_contents(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            UNIQUE(content_id, version_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            version_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            decision TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (content_id) REFERENCES text_contents(id),
            FOREIGN KEY (version_id) REFERENCES text_versions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # =========================================================
    # CONTENIDO VISUAL
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            FOREIGN KEY (project_id) REFERENCES projects(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            filename TEXT NOT NULL,
            prompt TEXT NOT NULL,
            style TEXT NOT NULL,
            seed INTEGER NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (content_id) REFERENCES image_contents(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            UNIQUE(content_id, version_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_review_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id INTEGER NOT NULL,
            version_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            comment TEXT NOT NULL,
            decision TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (content_id) REFERENCES image_contents(id),
            FOREIGN KEY (version_id) REFERENCES image_versions(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)


    # Tablas para contenido y chunks de RAG
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding TEXT,
            FOREIGN KEY (document_id)
                REFERENCES knowledge_documents(id)
                ON DELETE CASCADE
        )
    """)

    # =========================================================
    # DATOS INICIALES PARA LA PRÁCTICA
    # =========================================================
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, role)
        VALUES ('Ana', 'designer')
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, role)
        VALUES ('Carlos', 'writer')
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, role)
        VALUES ('Fran', 'approver')
        """
    )

    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (name, created_by)
        SELECT 'Campaña Otoño', id
        FROM users
        WHERE name = 'Carlos'
        """
    )

    connection.commit()
    connection.close()


# =============================================================
# USUARIOS
# =============================================================

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


# =============================================================
# PROYECTOS
# =============================================================

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


# =============================================================
# TEXTOS
# =============================================================

def create_text_content(
    project_id: int,
    title: str,
    created_by: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO text_contents (
            project_id,
            title,
            created_by,
            status
        )
        VALUES (?, ?, ?, 'draft')
        """,
        (project_id, title, created_by)
    )

    content_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return content_id


def save_text_version(
    content_id: int,
    text: str,
    action: str,
    created_by: int,
    created_at: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COALESCE(MAX(version_number), 0)
        FROM text_versions
        WHERE content_id = ?
        """,
        (content_id,)
    )

    current_version = cursor.fetchone()[0]
    next_version = current_version + 1

    cursor.execute(
        """
        INSERT INTO text_versions (
            content_id,
            version_number,
            text,
            action,
            created_by,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            content_id,
            next_version,
            text,
            action,
            created_by,
            created_at
        )
    )

    connection.commit()
    connection.close()

    return next_version


def get_text_contents(project_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, created_by, status
        FROM text_contents
        WHERE project_id = ?
        ORDER BY title
        """,
        (project_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "created_by": row[2],
            "status": row[3]
        }
        for row in rows
    ]


def get_text_versions(content_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            version_number,
            text,
            action,
            created_by,
            created_at
        FROM text_versions
        WHERE content_id = ?
        ORDER BY version_number DESC
        """,
        (content_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "version_number": row[1],
            "text": row[2],
            "action": row[3],
            "created_by": row[4],
            "created_at": row[5]
        }
        for row in rows
    ]


def update_text_content_status(
    content_id: int,
    status: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE text_contents
        SET status = ?
        WHERE id = ?
        """,
        (status, content_id)
    )

    connection.commit()
    connection.close()


def add_review_comment(
    content_id: int,
    version_id: int,
    user_id: int,
    comment: str,
    decision: str,
    created_at: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO review_comments (
            content_id,
            version_id,
            user_id,
            comment,
            decision,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            content_id,
            version_id,
            user_id,
            comment,
            decision,
            created_at
        )
    )

    connection.commit()
    connection.close()


def get_review_comments(content_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            version_id,
            user_id,
            comment,
            decision,
            created_at
        FROM review_comments
        WHERE content_id = ?
        ORDER BY created_at DESC
        """,
        (content_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "version_id": row[1],
            "user_id": row[2],
            "comment": row[3],
            "decision": row[4],
            "created_at": row[5]
        }
        for row in rows
    ]


# =============================================================
# IMÁGENES
# =============================================================

def create_image_content(
    project_id: int,
    title: str,
    created_by: int
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO image_contents (
            project_id,
            title,
            created_by,
            status
        )
        VALUES (?, ?, ?, 'draft')
        """,
        (project_id, title, created_by)
    )

    content_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return content_id


def save_image_version(
    content_id: int,
    filename: str,
    prompt: str,
    style: str,
    seed: int,
    created_by: int,
    created_at: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COALESCE(MAX(version_number), 0)
        FROM image_versions
        WHERE content_id = ?
        """,
        (content_id,)
    )

    current_version = cursor.fetchone()[0]
    next_version = current_version + 1

    cursor.execute(
        """
        INSERT INTO image_versions (
            content_id,
            version_number,
            filename,
            prompt,
            style,
            seed,
            created_by,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            content_id,
            next_version,
            filename,
            prompt,
            style,
            seed,
            created_by,
            created_at
        )
    )

    connection.commit()
    connection.close()

    return next_version


def get_image_contents(project_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, created_by, status
        FROM image_contents
        WHERE project_id = ?
        ORDER BY title
        """,
        (project_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "created_by": row[2],
            "status": row[3]
        }
        for row in rows
    ]


def get_image_versions(content_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            version_number,
            filename,
            prompt,
            style,
            seed,
            created_by,
            created_at
        FROM image_versions
        WHERE content_id = ?
        ORDER BY version_number DESC
        """,
        (content_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "version_number": row[1],
            "filename": row[2],
            "prompt": row[3],
            "style": row[4],
            "seed": row[5],
            "created_by": row[6],
            "created_at": row[7]
        }
        for row in rows
    ]


def update_image_content_status(
    content_id: int,
    status: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE image_contents
        SET status = ?
        WHERE id = ?
        """,
        (status, content_id)
    )

    connection.commit()
    connection.close()


def add_image_review_comment(
    content_id: int,
    version_id: int,
    user_id: int,
    comment: str,
    decision: str,
    created_at: str
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO image_review_comments (
            content_id,
            version_id,
            user_id,
            comment,
            decision,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            content_id,
            version_id,
            user_id,
            comment,
            decision,
            created_at
        )
    )

    connection.commit()
    connection.close()


def get_image_review_comments(content_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            version_id,
            user_id,
            comment,
            decision,
            created_at
        FROM image_review_comments
        WHERE content_id = ?
        ORDER BY created_at DESC
        """,
        (content_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "id": row[0],
            "version_id": row[1],
            "user_id": row[2],
            "comment": row[3],
            "decision": row[4],
            "created_at": row[5]
        }
        for row in rows
    ]


def delete_image_version_by_filename(filename: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM image_versions
        WHERE filename = ?
        """,
        (filename,)
    )

    connection.commit()
    connection.close()


# ============================================================
# KNOWLEDGE / RAG
# ============================================================

def create_knowledge_document(
    project_id: int,
    title: str,
    content: str,
    content_hash: str,
    created_at: str
) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO knowledge_documents (
            project_id,
            title,
            content,
            content_hash,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            project_id,
            title,
            content,
            content_hash,
            created_at
        )
    )

    document_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return document_id


def get_knowledge_document(
    project_id: int,
    title: str
) -> dict | None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            project_id,
            title,
            content,
            content_hash,
            created_at
        FROM knowledge_documents
        WHERE project_id = ?
          AND title = ?
        LIMIT 1
        """,
        (
            project_id,
            title
        )
    )

    row = cursor.fetchone()
    connection.close()

    return dict(row) if row else None


def update_knowledge_document(
    document_id: int,
    content: str,
    content_hash: str,
    created_at: str
) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE knowledge_documents
        SET
            content = ?,
            content_hash = ?,
            created_at = ?
        WHERE id = ?
        """,
        (
            content,
            content_hash,
            created_at,
            document_id
        )
    )

    connection.commit()
    connection.close()


def delete_knowledge_chunks(
    document_id: int
) -> None:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM knowledge_chunks
        WHERE document_id = ?
        """,
        (document_id,)
    )

    connection.commit()
    connection.close()

def save_knowledge_chunk(
    document_id: int,
    chunk_index: int,
    chunk_text: str,
    embedding: list[float]
) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO knowledge_chunks (
            document_id,
            chunk_index,
            chunk_text,
            embedding
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            document_id,
            chunk_index,
            chunk_text,
            json.dumps(embedding)
        )
    )

    chunk_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return chunk_id    

def get_knowledge_chunks(
    project_id: int
) -> list[dict]:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            kc.id,
            kc.document_id,
            kc.chunk_index,
            kc.chunk_text,
            kc.embedding,
            kd.title AS document_title
        FROM knowledge_chunks kc
        INNER JOIN knowledge_documents kd
            ON kd.id = kc.document_id
        WHERE kd.project_id = ?
        ORDER BY
            kc.document_id,
            kc.chunk_index
        """,
        (project_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    chunks = []

    for row in rows:
        chunk = dict(row)

        if chunk["embedding"]:
            chunk["embedding"] = json.loads(
                chunk["embedding"]
            )

        chunks.append(chunk)

    return chunks