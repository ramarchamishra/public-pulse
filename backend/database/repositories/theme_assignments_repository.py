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