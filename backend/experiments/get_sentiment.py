import time

from database.repositories.tweets_repository import get_tweets_by_search
from services.sentiment.roberta_sentiment import RobertaSentiment


SEARCH_ID = 6


def main():

    tweets = get_tweets_by_search(
        search_id=SEARCH_ID
    )

    print(f"Fetched {len(tweets)} tweets.\n")

    sentiment = RobertaSentiment()

    start = time.perf_counter()

    results = []

    for tweet in tweets:

        label, confidence = sentiment.analyze(tweet)

        results.append((label, confidence))

    end = time.perf_counter()

    print(f"Analyzed {len(results)} tweets")
    print(f"Time Taken : {end - start:.2f} seconds")
    print(f"Average    : {(end - start)/len(results):.4f} sec/tweet\n")

    print("First 10 Results:\n")

    for i, (tweet, result) in enumerate(zip(tweets, results), start=1):

        if i > 10:
            break

        label, confidence = result

        print(f"{i}. {label:9} ({confidence:.4f})")
        print(tweet.text[:120])
        print("-" * 80)


if __name__ == "__main__":
    main()