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


def get_tweets_for_theme(
    run_id: int,
    bertopic_topic_id: int,
    model_name: str,
    limit: int = 5
) -> list[dict]:
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    if bertopic_topic_id < -1:
        raise ValueError("bertopic_topic_id must be -1 or greater")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                t.tweet_id,
                t.text,
                t.author,
                t.created_at,
                ta.theme_id,
                ta.bertopic_topic_id,
                ta.probability AS theme_probability,
                sr.label AS sentiment_label,
                sr.confidence AS sentiment_confidence

            FROM theme_assignments ta

            JOIN tweets t
                ON t.tweet_id = ta.tweet_id

            LEFT JOIN sentiment_results sr
                ON sr.tweet_id = ta.tweet_id
                AND sr.model_name = ?

            WHERE ta.run_id = ?
              AND ta.bertopic_topic_id = ?

            ORDER BY
                ta.probability DESC,
                t.tweet_id ASC

            LIMIT ?
        """, (
            model_name,
            run_id,
            bertopic_topic_id,
            limit
        ))

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:
        connection.close()