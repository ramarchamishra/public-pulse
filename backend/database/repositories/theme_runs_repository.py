import sqlite3
from database.connection import get_connection


def create_theme_run(
    connection: sqlite3.Connection,
    search_id: int,
    embedding_model: str,
    pipeline_version: str
) -> int:
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO theme_discovery_runs (
            search_id,
            embedding_model,
            pipeline_version
        )
        VALUES (?, ?, ?)
    """, (
        search_id,
        embedding_model,
        pipeline_version
    ))

    run_id = cursor.lastrowid

    if run_id is None:
        raise RuntimeError("Failed to create theme discovery run")

    return run_id


def get_latest_theme_run(
    search_id: int
) -> sqlite3.Row | None:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                search_id,
                embedding_model,
                pipeline_version,
                created_at
            FROM theme_discovery_runs
            WHERE search_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (search_id,))

        return cursor.fetchone()

    finally:
        connection.close()