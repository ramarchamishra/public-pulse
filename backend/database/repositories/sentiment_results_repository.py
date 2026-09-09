from database.connection import get_connection

def get_sentiment_statistics(search_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            sr.label,
            COUNT(*) AS tweet_count,
            AVG(sr.confidence) AS average_confidence

        FROM sentiment_results sr

        JOIN search_tweets st
            ON sr.tweet_id = st.tweet_id

        WHERE st.search_id = ?

        GROUP BY sr.label
    """, (search_id,))

    rows = cursor.fetchall()

    connection.close()

    return rows

def save_sentiment(
    tweet_id: str,
    model_name: str,
    label: str,
    confidence: float
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO sentiment_results (
            tweet_id,
            model_name,
            label,
            confidence
        )
        VALUES (?, ?, ?, ?)
        
        ON CONFLICT(tweet_id, model_name)
        DO UPDATE SET
            label = excluded.label,
            confidence = excluded.confidence,
            analyzed_at = CURRENT_TIMESTAMP
    """, (
        tweet_id,
        model_name,
        label,
        confidence
    ))

    connection.commit()
    connection.close()

def get_analyzed_tweet_ids_for_search(
    search_id: int,
    model_name: str
) -> set[str]:
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT sr.tweet_id
            FROM sentiment_results sr

            JOIN search_tweets st
                ON st.tweet_id = sr.tweet_id

            WHERE st.search_id = ?
              AND sr.model_name = ?
        """, (search_id, model_name))

        return {
            str(row["tweet_id"])
            for row in cursor.fetchall()
        }

    finally:
        connection.close()