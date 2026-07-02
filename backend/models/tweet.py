from dataclasses import dataclass


@dataclass(slots=True)
class Tweet:
    tweet_id: str
    text: str
    author: str
    created_at: str
    favorite_count: int
    retweet_count: int
    language: str | None = None