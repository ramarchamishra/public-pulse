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
import time
import csv
from models.tweet import Tweet


PAGES_BEFORE_COOLDOWN = 42      
COOLDOWN_SECONDS = 10 * 60      # proactive pause, no request made during this time
MIN_YIELD_PER_CYCLE = 20   # stop — soft-throttled or exhausted


class TwikitScraper(ScraperInterface):

    def __init__(self):
        self.client = Client(
            'en-US',
            user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0"
        )

    async def load_session(self):
        self.client.set_cookies({
            "auth_token": Config.X_AUTHTOKEN,
            "ct0": Config.X_CT0,
            "guest_id":Config.X_GUEST_ID,
            "guest_id_ads":Config.X_GUEST_ID_ADS,
            "guest_id_marketing":Config.X_GUEST_ID_MARKETING,
            "personalization_id":Config.X_PERSONALIZATION_ID,
            "twid":Config.X_TWID
        })

    def _dump_rate_limit_info(self, e: Exception):
        """Print whatever diagnostic info we can find on the exception, so we can
        figure out the real reset window instead of guessing."""
        print("---- Rate limit diagnostic dump ----")
        print(f"repr: {e!r}")
        for attr in ("headers", "response", "args"):
            if hasattr(e, attr):
                val = getattr(e, attr)
                print(f"{attr}: {val}")
                # if it's a response object, headers are usually nested one level deeper
                if attr == "response" and val is not None and hasattr(val, "headers"):
                    print(f"response.headers: {dict(val.headers)}")
        print("-------------------------------------")

    async def get_tweets(self, topic: str, mode:str = "Latest",limit = 100):

        results = []
        rejected = []

        if(mode=="Latest" or mode=="Top"):
            results,rejected,pages_since_cooldown = await self.scrape_tweets(topic=topic,limit=limit,mode=mode)

        elif(mode=="Mixed"):
            top_limit = int(min(600,0.5*limit))
            temp_res,temp_rej,pages_since_cooldown = await self.scrape_tweets(topic=topic,limit=top_limit,mode="Top")
            results.extend(temp_res)
            rejected.extend(temp_rej)

            limit = max(0, limit - len(results))
            temp_res,temp_rej,pages_since_cooldown = await self.scrape_tweets(topic=topic,
                                                  limit=limit,
                                                  mode="Latest",
                                                  seen_ids=set(t.tweet_id for t in results),
                                                  pages_since_cooldown=pages_since_cooldown)
            results.extend(temp_res)
            rejected.extend(temp_rej)
            print(f"Mixed Mode Results: Tweet Total:{len(results)}, Rejected: {len(rejected)}, ")

        else: raise ValueError(f"Unknown mode: {mode}")

        try:
            with open("last_run.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "tweet_id", "text", "author", "created_at",
                    "favorite_count", "retweet_count", "language",
                ])
                writer.writeheader()
                for t in results:
                    writer.writerow({
                        "tweet_id": t.tweet_id,
                        "text": t.text,
                        "author": t.author,
                        "created_at": t.created_at,
                        "favorite_count": t.favorite_count,
                        "retweet_count": t.retweet_count,
                        "language": t.language,
                    })

            with open("last_run_rejected.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["tweet_id", "text", "reason", "language"])
                writer.writeheader()
                writer.writerows(rejected)

            print(f"Saved {len(results)} tweets to last_run.csv, "
                  f"{len(rejected)} rejected tweets to last_run_rejected.csv")
        except Exception as e:
            print(f"Failed to write CSV files: {e}")



        return results

    async def scrape_tweets(self, topic: str, mode: str, limit: int = 100,seen_ids:set = None,pages_since_cooldown: int = 0):
        results = []

        query_tokens = build_variant_patterns(extract_query_tokens(topic))
        search_query = f"{topic} lang:en -is:retweet"

        seen_ids = seen_ids if seen_ids is not None else set()
        rejected = []
        dropped_irrelevant, dropped_short, dropped_duplicates = 0, 0, 0
        page_count = 0
        rate_limited = False
        start_time = time.monotonic()
        results_at_last_cooldown = 0
        stalled = False
        cooldown_count = 0

        MAX_COOLDOWNS = max(2,limit//300)          # hard ceiling on cooldown cycles per run

        try:
            tweets = await self.client.search_tweet(search_query, product=mode, count=20)

            while tweets is not None and len(results) < limit:

                for tweet in tweets:
                    if getattr(tweet, "lang", None) != "en":
                        rejected.append({
                            "tweet_id": tweet.id,
                            "text": (tweet.text or "").strip(),
                            "reason": "non_english",
                            "language": getattr(tweet, "lang", None),
                        })
                        continue
                    elif tweet.id in seen_ids:
                        dropped_duplicates += 1
                        rejected.append({
                            "tweet_id": tweet.id,
                            "text": (tweet.text or "").strip(),
                            "reason": "duplicate",
                            "language": getattr(tweet, "lang", None),
                        })
                        continue
                    elif not tweet.text or len(tweet.text.strip()) < 10:
                        dropped_short += 1
                        rejected.append({
                            "tweet_id": tweet.id,
                            "text": (tweet.text or "").strip(),
                            "reason": "too_short",
                            "language": getattr(tweet, "lang", None),
                        })
                        continue
                    elif not is_relevant(tweet.text, query_tokens):
                        dropped_irrelevant += 1
                        rejected.append({
                            "tweet_id": tweet.id,
                            "text": tweet.text.strip(),
                            "reason": "irrelevant",
                            "language": getattr(tweet, "lang", None),
                        })
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
                pages_since_cooldown += 1
                if len(results) >= limit:
                    break

                if pages_since_cooldown >= PAGES_BEFORE_COOLDOWN:
                    cycle_yield = len(results) - results_at_last_cooldown

                    if cycle_yield < MIN_YIELD_PER_CYCLE:
                        print(f"Only {cycle_yield} new tweets in the last {pages_since_cooldown} pages — "
                              f"likely soft-throttled or query exhausted. Stopping ({len(results)} collected).")
                        stalled = True
                        break

                    if limit<700:
                        if len(results)>(97/100*limit):
                            print("Tweets close to target collected, Not worth another Cooldown")
                            break
                    elif len(results)>(95/100*limit):
                            print("Tweets close to target collected, Not worth another Cooldown")
                            break

                    cooldown_count += 1
                    if cooldown_count > MAX_COOLDOWNS:
                        print(f"Hit max cooldowns ({MAX_COOLDOWNS}) — stopping, ({len(results)} collected).")
                        break

                    print(f"Hit {pages_since_cooldown} pages without a rate limit — "
                          f"cooling down for {COOLDOWN_SECONDS}s before continuing "
                          f"({len(results)} tweets collected so far, +{cycle_yield} this cycle).")
                    elapsed = time.monotonic() - start_time
                    print(f"Time taken till now: {elapsed:.2f}s ({elapsed/60:.2f} min)")
                    await asyncio.sleep(COOLDOWN_SECONDS)
                    pages_since_cooldown = 0
                    results_at_last_cooldown = len(results)
                    print("Cooldown Over, Starting again...")

                tweets = await tweets.next()
                await asyncio.sleep(random.uniform(4, 8))  # base pacing between pages

        except TooManyRequests as e:
            rate_limited = True
            print(f"Rate limited after {page_count} pages, {len(results)} tweets collected. "
                  f"Terminating run — not retrying.")
            self._dump_rate_limit_info(e)

        except Exception as e:
            print(f"Unexpected error after {page_count} pages, {len(results)} tweets collected: {e}")

        print(f"Fetched relevant: {len(results)}, Dropped irrelevant: {dropped_irrelevant}, "
              f"Pages: {page_count}, Dropped Short: {dropped_short}, Dropped Duplicates: {dropped_duplicates}, mode: {mode}, "
              f"Rate limited:{rate_limited}, Stalled:{stalled}, Cooldowns used: {cooldown_count}")
        elapsed = time.monotonic() - start_time
        print(f"Total time taken: {elapsed:.2f}s ({elapsed/60:.2f} min)")


        return results[:limit],rejected,pages_since_cooldown