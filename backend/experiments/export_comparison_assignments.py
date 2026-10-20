
import csv
from pathlib import Path

from database.repositories.tweets_repository import get_tweets_by_search
from services.comparisons.search_comparison_service import (
    SearchComparisonService,
)


def main():
    search_id_a = int(input("First search ID: "))
    search_id_b = int(input("Second search ID: "))

    service = SearchComparisonService()

    discovery = service.discover_shared_themes(
        search_id_a,
        search_id_b
    )

    assignments = discovery["topic_assignments"]

    rows = []

    for search_id in (search_id_a, search_id_b):
        tweets = get_tweets_by_search(search_id)

        for tweet in tweets:
            rows.append({
                "topic_id": assignments[tweet.tweet_id],
                "search_id": search_id,
                "tweet_id": tweet.tweet_id,
                "text": tweet.text,
            })

    # Group rows by topic, then by source search.
    # Keep noise at the end.
    rows.sort(
        key=lambda row: (
            row["topic_id"] == -1,
            row["topic_id"],
            row["search_id"],
            row["tweet_id"],
        )
    )

    expected_count = (
        discovery["tweet_count_a"]
        + discovery["tweet_count_b"]
    )

    if len(rows) != expected_count:
        raise RuntimeError("Export row count mismatch")

    output_path = Path(
        f"comparison_{search_id_a}_{search_id_b}_assignments.csv"
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "topic_id",
                "search_id",
                "tweet_id",
                "text",
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print("\nComparison export completed!")
    print("File:", output_path.resolve())
    print("Rows exported:", len(rows))
    print("Unique tweets:", discovery["unique_tweet_count"])
    print("Discovered themes:", discovery["theme_count"])
    print("Noise tweets:", discovery["noise_count"])


if __name__ == "__main__":
    main()
