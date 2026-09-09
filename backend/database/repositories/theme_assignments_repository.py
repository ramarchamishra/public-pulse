import sqlite3
from database.connection import get_connection


def create_theme_assignments(
    connection: sqlite3.Connection,
    run_id: int,
    assignments: list[
        tuple[str, int | None, int, float | None]
    ]
) -> None:
    cursor = connection.cursor()

    rows = [
        (
            run_id,
            tweet_id,
            theme_id,
            bertopic_topic_id,
            probability
        )
        for (
            tweet_id,
            theme_id,
            bertopic_topic_id,
            probability
        ) in assignments
    ]

    cursor.executemany("""
        INSERT INTO theme_assignments (
            run_id,
            tweet_id,
            theme_id,
            bertopic_topic_id,
            probability
        )
        VALUES (?, ?, ?, ?, ?)
    """, rows)

def get_assignment_statistics_for_run(
    run_id: int
) -> dict:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) AS total_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN bertopic_topic_id >= 0 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS clustered_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN bertopic_topic_id = -1 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS noise_count,

                AVG(probability) AS average_probability

            FROM theme_assignments
            WHERE run_id = ?
        """, (run_id,))

        row = cursor.fetchone()

        return {
            "total_count": row["total_count"],
            "clustered_count": row["clustered_count"],
            "noise_count": row["noise_count"],
            "average_probability": row["average_probability"],
        }

    finally:
        connection.close()


def get_theme_sentiment_statistics_for_run(
    run_id: int,
    model_name: str
) -> list[dict]:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                ta.theme_id,
                ta.bertopic_topic_id,
                sr.label,
                COUNT(*) AS tweet_count,
                AVG(sr.confidence) AS average_confidence

            FROM theme_assignments ta

            LEFT JOIN sentiment_results sr
                ON sr.tweet_id = ta.tweet_id
                AND sr.model_name = ?

            WHERE ta.run_id = ?

            GROUP BY
                ta.theme_id,
                ta.bertopic_topic_id,
                sr.label

            ORDER BY
                ta.bertopic_topic_id ASC,
                sr.label ASC
        """, (model_name, run_id))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()