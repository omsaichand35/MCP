import json
import sqlite3
from datetime import datetime


HISTORY_DB_PATH = "sql_query_history.db"


def get_history_connection():
    return sqlite3.connect(HISTORY_DB_PATH)


def initialize_history_store():
    connection = get_history_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS query_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            sql TEXT NOT NULL,
            query_type TEXT NOT NULL,
            validation_result TEXT NOT NULL,
            execution_result TEXT NOT NULL,
            approved INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def record_query_history(
    question: str,
    sql: str,
    query_type: str,
    validation_result: dict,
    execution_result: dict,
    approved: bool = False,
):
    initialize_history_store()
    connection = get_history_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO query_history (
            question,
            sql,
            query_type,
            validation_result,
            execution_result,
            approved,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            question,
            sql,
            query_type,
            json.dumps(validation_result, default=str),
            json.dumps(execution_result, default=str),
            1 if approved else 0,
            datetime.utcnow().isoformat(),
        ),
    )

    connection.commit()
    connection.close()


def get_query_history(limit: int = 25):
    initialize_history_store()
    connection = get_history_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            sql,
            query_type,
            validation_result,
            execution_result,
            approved,
            created_at
        FROM query_history
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]