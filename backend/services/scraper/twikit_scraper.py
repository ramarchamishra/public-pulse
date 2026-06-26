import utils.twikit_patch
import httpx
httpx._config.DEFAULT_TIMEOUT_CONFIG = httpx.Timeout(30.0)
from twikit import Client
from services.scraper.scraper_interface import ScraperInterface
from utils.config import Config
import asyncio


class TwikitScraper(ScraperInterface):

    def __init__(self):
        self.client = Client('en-US')

    async def load_session(self):
            self.client.set_cookies({
            "auth_token": Config.X_AUTHTOKEN,
            "ct0": Config.X_CT0,
        })

    async def get_tweets(self, topic: str, limit: int = 100):
        results = []
        tweets = await self.client.search_tweet(topic, product='Latest', count=20)
    
        while tweets and len(results) < limit:
            for tweet in tweets:
                results.append({
                    "tweet_id": tweet.id,
                    "text": tweet.text,
                    "author": tweet.user.screen_name,
                    "created_at": tweet.created_at,
                    "retweet_count": tweet.retweet_count,
                    "favorite_count": tweet.favorite_count,
                })
        
            if len(results) >= limit:
                break
            
            # Fetch next page
            tweets = await tweets.next()
            await asyncio.sleep(1)  # avoid rate limiting
    
        return results[:limit]