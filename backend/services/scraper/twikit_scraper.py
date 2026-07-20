import utils.twikit_patch
import httpx
httpx._config.DEFAULT_TIMEOUT_CONFIG = httpx.Timeout(30.0)
from twikit import Client
from services.scraper.scraper_interface import ScraperInterface
from utils.config import Config
import asyncio
from models.tweet import Tweet


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
        topic = f"{topic} lang:en -is:retweet"
        tweets = await self.client.search_tweet(topic, product='Latest', count=20)

        seen_ids = set()
    
        while tweets is not None and len(results) < limit:
            
            for tweet in tweets:
                if getattr(tweet, "lang", None) != "en":
                    continue

                if tweet.id in seen_ids:
                    continue
                
                if not tweet.text or len(tweet.text.strip()) < 6:
                    continue


                seen_ids.add(tweet.id)
                results.append(
                    Tweet(
                        tweet_id=tweet.id,
                        text=tweet.text.strip(),
                        author=tweet.user.screen_name,
                        created_at=str(tweet.created_at),
                        favorite_count=tweet.favorite_count,
                        retweet_count=tweet.retweet_count,
                        language=getattr(tweet, "lang", None),
                    )
                )
        
            if len(results) >= limit:
                break
            
            # Fetch next page
            tweets = await tweets.next()
            await asyncio.sleep(1)  # avoid rate limiting
    
        return results[:limit]