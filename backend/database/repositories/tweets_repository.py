from database.connection import get_connection


def save_tweet(tweet: dict):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO tweets (
            tweet_id,
            text,
            author,
            created_at,
            favorite_count,
            retweet_count,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(tweet_id)
        DO UPDATE SET
            text = excluded.text,
            author = excluded.author,
            favorite_count = excluded.favorite_count,
            retweet_count = excluded.retweet_count,
            language = excluded.language
    """, (
        tweet["tweet_id"],
        tweet["text"],
        tweet["author"],
        tweet["created_at"],
        tweet["favorite_count"],
        tweet["retweet_count"],
        tweet["language"]
    ))

    connection.commit()
    connection.close()