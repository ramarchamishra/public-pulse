from database.connection import get_connection


def link_tweet_to_search(search_id: int, tweet_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO search_tweets (
            search_id,
            tweet_id
        )
        VALUES (?, ?)
    """, (search_id, tweet_id))

    connection.commit()
    connection.close()