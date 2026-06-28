from database.connection import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        requested_limit INTEGER NOT NULL,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tweets (
        tweet_id TEXT PRIMARY KEY,
        text TEXT NOT NULL,
        author TEXT NOT NULL,
        created_at TEXT,
        last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        favorite_count INTEGER DEFAULT 0,
        retweet_count INTEGER DEFAULT 0,
        language TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_tweets (
        search_id INTEGER,
        tweet_id TEXT,

        PRIMARY KEY (search_id, tweet_id),

        FOREIGN KEY (search_id)
            REFERENCES searches(id)
            ON DELETE CASCADE,

        FOREIGN KEY (tweet_id)
            REFERENCES tweets(tweet_id)
            ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sentiment_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        tweet_id TEXT NOT NULL,

        model_name TEXT NOT NULL,

        label TEXT NOT NULL,

        confidence REAL NOT NULL,

        analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (tweet_id)
            REFERENCES tweets(tweet_id)
            ON DELETE CASCADE,
                   
        UNIQUE(tweet_id, model_name)
    )
    """)

    connection.commit()
    connection.close()