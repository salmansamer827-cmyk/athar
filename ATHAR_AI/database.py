import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            step_number INTEGER NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(task_id) REFERENCES tasks(id)
        )
    """)

    conn.commit()
    conn.close()


def create_task(task):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    cursor = conn.execute(
        """
        INSERT INTO tasks
        (task, status, created_at)
        VALUES (?, ?, ?)
        """,
        (task, "running", now)
    )

    task_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return task_id


def complete_task(task_id, result):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    conn.execute(
        """
        UPDATE tasks
        SET status = ?,
            result = ?,
            completed_at = ?
        WHERE id = ?
        """,
        ("completed", result, now, task_id)
    )

    conn.commit()
    conn.close()


def fail_task(task_id, error):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    conn.execute(
        """
        UPDATE tasks
        SET status = ?,
            result = ?,
            completed_at = ?
        WHERE id = ?
        """,
        ("failed", error, now, task_id)
    )

    conn.commit()
    conn.close()


def add_step(task_id, step_number, description):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    cursor = conn.execute(
        """
        INSERT INTO task_steps
        (task_id, step_number, description, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            task_id,
            step_number,
            description,
            "pending",
            now
        )
    )

    step_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return step_id


def update_step(step_id, status, result=None):
    conn = get_connection()

    conn.execute(
        """
        UPDATE task_steps
        SET status = ?,
            result = ?
        WHERE id = ?
        """,
        (status, result, step_id)
    )

    conn.commit()
    conn.close()


def save_memory(key, value):
    conn = get_connection()

    now = datetime.utcnow().isoformat()

    conn.execute(
        """
        INSERT INTO memories
        (key, value, created_at)
        VALUES (?, ?, ?)
        """,
        (key, value, now)
    )

    conn.commit()
    conn.close()


def get_memories(limit=20):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT key, value, created_at
        FROM memories
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_tasks(limit=20):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM tasks
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]
