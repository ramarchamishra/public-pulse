import json
import sqlite3


def create_theme(
    connection: sqlite3.Connection,
    run_id: int,
    bertopic_topic_id: int,
    name: str,
    keywords: list[tuple[str, float]]
) -> int:
    cursor = connection.cursor()

    keywords_json = json.dumps(keywords)

    cursor.execute("""
        INSERT INTO themes (
            run_id,
            bertopic_topic_id,
            name,
            keywords
        )
        VALUES (?, ?, ?, ?)
    """, (
        run_id,
        bertopic_topic_id,
        name,
        keywords_json
    ))

    theme_id = cursor.lastrowid

    if theme_id is None:
        raise RuntimeError("Failed to create theme")

    return theme_id