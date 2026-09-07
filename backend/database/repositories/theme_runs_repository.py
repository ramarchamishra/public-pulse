import sqlite3


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