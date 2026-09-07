import sqlite3


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