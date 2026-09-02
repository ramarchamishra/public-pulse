from database.connection import get_connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        requested_limit INTEGER NOT NULL,
        mode TEXT NOT NULL,
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS theme_discovery_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_id INTEGER NOT NULL,
        embedding_model TEXT NOT NULL,
        pipeline_version TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (search_id)
            REFERENCES searches(id)
            ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS themes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        bertopic_topic_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        keywords TEXT NOT NULL,

        FOREIGN KEY (run_id)
            REFERENCES theme_discovery_runs(id)
            ON DELETE CASCADE,

        UNIQUE (run_id, bertopic_topic_id),
        CHECK (bertopic_topic_id >= 0)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS theme_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        tweet_id TEXT NOT NULL,
        theme_id INTEGER,
        bertopic_topic_id INTEGER NOT NULL,
        probability REAL,

        FOREIGN KEY (run_id)
            REFERENCES theme_discovery_runs(id)
            ON DELETE CASCADE,

        FOREIGN KEY (tweet_id)
            REFERENCES tweets(tweet_id)
            ON DELETE CASCADE,

        FOREIGN KEY (theme_id)
            REFERENCES themes(id)
            ON DELETE CASCADE,

        UNIQUE (run_id, tweet_id),

        CHECK (
            (bertopic_topic_id = -1 AND theme_id IS NULL)
            OR
            (bertopic_topic_id >= 0 AND theme_id IS NOT NULL)
        ),

        CHECK (
            probability IS NULL
            OR probability BETWEEN 0.0 AND 1.0
        )
    )
    """)

    connection.commit()
    connection.close()

