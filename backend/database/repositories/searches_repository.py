from database.connection import get_connection


def create_search(topic: str, requested_limit: int) -> int:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO searches (topic, requested_limit)
        VALUES (?, ?)
    """, (topic, requested_limit))

    search_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return search_id