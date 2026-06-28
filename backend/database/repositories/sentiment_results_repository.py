from database.connection import get_connection


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