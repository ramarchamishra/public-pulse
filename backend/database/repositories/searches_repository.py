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