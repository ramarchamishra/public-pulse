from database.repositories.searches_repository import create_search
from database.repositories.tweets_repository import save_tweet
from database.repositories.search_tweets_repository import link_tweet_to_search

from services.scraper.twikit_scraper import TwikitScraper


class IngestionService:

    def __init__(self):
        self.scraper = TwikitScraper()

    async def ingest_topic(
        self,
        topic: str,
        limit: int = 100,
        mode: str = "Latest"
    ):
        
        search_id = create_search(topic, limit, mode)

        await self.scraper.load_session()

        tweets = await self.scraper.get_tweets(topic=topic, limit=limit, mode=mode)

        for tweet in tweets:

            save_tweet(tweet)

            link_tweet_to_search(
                search_id,
                tweet.tweet_id
            )

        return {
            "search_id": search_id,
            "tweets_saved": len(tweets)
        }