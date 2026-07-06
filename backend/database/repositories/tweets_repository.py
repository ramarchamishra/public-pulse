from database.connection import get_connection
from models.tweet import Tweet

def get_unanalyzed_tweets(limit: int = 100) -> list[Tweet]:

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM tweets
        WHERE tweet_id NOT IN (
            SELECT tweet_id
            FROM sentiment_results
        )
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    tweets = []

    for row in rows:
        tweets.append(
            Tweet(
                tweet_id=row["tweet_id"],
                text=row["text"],
                author=row["author"],
                created_at=row["created_at"],
                favorite_count=row["favorite_count"],
                retweet_count=row["retweet_count"],
                language=row["language"],
            )
        )

    return tweets

def save_tweet(tweet: Tweet):
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
        tweet.tweet_id,
        tweet.text,
        tweet.author,
        tweet.created_at,
        tweet.favorite_count,
        tweet.retweet_count,
        tweet.language
    ))

    connection.commit()
    connection.close()