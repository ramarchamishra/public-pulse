from database.connection import get_connection


def create_search(topic: str, requested_limit: int, mode: str) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO searches (topic, requested_limit,mode)
        VALUES (?, ?, ?)
    """, (topic, requested_limit, mode))

    search_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return search_id

def get_search_topic(search_id: int) -> str | None:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT topic
            FROM searches
            WHERE id = ?
            """,
            (search_id,)
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return row["topic"]

    finally:
        connection.close()