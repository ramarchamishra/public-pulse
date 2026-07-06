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