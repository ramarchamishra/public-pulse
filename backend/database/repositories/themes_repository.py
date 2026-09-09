import json
import sqlite3
from database.connection import get_connection


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

def get_themes_for_run(run_id: int) -> list[dict]:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                t.id,
                t.run_id,
                t.bertopic_topic_id,
                t.name,
                t.keywords,
                COUNT(ta.id) AS tweet_count
            FROM themes t

            LEFT JOIN theme_assignments ta
                ON ta.theme_id = t.id
                AND ta.run_id = t.run_id

            WHERE t.run_id = ?

            GROUP BY
                t.id,
                t.run_id,
                t.bertopic_topic_id,
                t.name,
                t.keywords

            ORDER BY
                tweet_count DESC,
                t.bertopic_topic_id ASC
        """, (run_id,))

        rows = cursor.fetchall()

        return [
            {
                "id": row["id"],
                "run_id": row["run_id"],
                "bertopic_topic_id": row["bertopic_topic_id"],
                "name": row["name"],
                "keywords": json.loads(row["keywords"]),
                "tweet_count": row["tweet_count"],
            }
            for row in rows
        ]

    finally:
        connection.close()