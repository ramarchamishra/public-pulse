import utils.twikit_patch
import httpx
httpx._config.DEFAULT_TIMEOUT_CONFIG = httpx.Timeout(30.0)
from twikit import Client
from twikit.errors import TooManyRequests
from services.scraper.scraper_interface import ScraperInterface
from services.filtering.relevance_filter import (
    extract_query_tokens,
    build_variant_patterns,
    is_relevant,
)
from utils.config import Config
import asyncio
import random
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

        query_tokens = build_variant_patterns(extract_query_tokens(topic))
        search_query = f"{topic} lang:en -is:retweet"

        seen_ids = set()
        dropped_irrelevant, dropped_short, dropped_duplicates = 0, 0, 0
        page_count = 0

        try:
            tweets = await self.client.search_tweet(search_query, product='Top', count=20)

            while tweets is not None and len(results) < limit:

                for tweet in tweets:
                    if getattr(tweet, "lang", None) != "en":
                        continue

                    if tweet.id in seen_ids:
                        dropped_duplicates += 1
                        continue

                    if not tweet.text or len(tweet.text.strip()) < 10:
                        dropped_short += 1
                        continue

                    if not is_relevant(tweet.text, query_tokens):
                        dropped_irrelevant += 1
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

                page_count += 1
                if len(results) >= limit:
                    break

                tweets = await tweets.next()
                await asyncio.sleep(random.uniform(4,8))  # avoid rate limiting

        except TooManyRequests as e:
            print(f"Rate limited after {page_count} pages, {len(results)} tweets collected. "
                  f"Returning partial results. ({e})")

        except Exception as e:
            # Catch-all so any other transient/network error doesn't lose the run either.
            print(f"Unexpected error after {page_count} pages, {len(results)} tweets collected: {e}")

        print(f"Fetched relevant: {len(results)}, Dropped irrelevant: {dropped_irrelevant}, "
              f"Pages: {page_count}, Dropped Short: {dropped_short}, Dropped Duplicates: {dropped_duplicates}")

        return results[:limit]