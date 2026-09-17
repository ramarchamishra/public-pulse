import time
from pprint import pprint

from database.connection import get_connection
from services.analysis.analysis_service import AnalysisService
from utils.config import Config


def main():
    search_id = int(input("Enter search ID: "))

    if str(Config.DEVICE).split(":")[0].lower() != "cuda":
        raise RuntimeError("Configure CUDA before running sentiment analysis")

    service = AnalysisService()

    start = time.perf_counter()
    result = service.analyze_search(search_id)
    elapsed = time.perf_counter() - start

    print("\nAnalysis result:")
    pprint(result)
    print(f"Time taken: {elapsed:.2f} seconds (excluding model loading)")

    analyzed_count = result["tweets_analyzed"]

    if analyzed_count:
        print(
            "Average including database saves: "
            f"{elapsed / analyzed_count:.4f} sec/new tweet"
        )
    else:
        print("All tweets already have sentiment for this model.")

    # Read only this search's saved results for the selected model.
    connection = get_connection()

    try:
        statistics = connection.execute("""
            SELECT
                sr.label,
                COUNT(*) AS tweet_count,
                AVG(sr.confidence) AS average_confidence
            FROM sentiment_results sr
            JOIN search_tweets st ON st.tweet_id = sr.tweet_id
            WHERE st.search_id = ?
              AND sr.model_name = ?
            GROUP BY sr.label
            ORDER BY sr.label
        """, (search_id, result["model_name"])).fetchall()

        examples = connection.execute("""
            SELECT
                t.tweet_id,
                t.text,
                sr.label,
                sr.confidence
            FROM sentiment_results sr
            JOIN search_tweets st ON st.tweet_id = sr.tweet_id
            JOIN tweets t ON t.tweet_id = sr.tweet_id
            WHERE st.search_id = ?
              AND sr.model_name = ?
            ORDER BY t.tweet_id ASC
            LIMIT 10
        """, (search_id, result["model_name"])).fetchall()

    finally:
        connection.close()

    total_saved = sum(row["tweet_count"] for row in statistics)

    print("\nSaved sentiment distribution:")
    for row in statistics:
        pprint(dict(row))

    print("\nSaved results for this search and model:", total_saved)

    if total_saved != result["tweets_found"]:
        raise RuntimeError(
            "Sentiment coverage mismatch: "
            f"expected={result['tweets_found']}, saved={total_saved}"
        )

    print("Sentiment coverage check passed")
    print("\nFirst 10 saved results (ordered by tweet ID):")

    for index, row in enumerate(examples, start=1):
        print(
            f"\n{index}. {row['label']:9} "
            f"({row['confidence']:.4f}) | Tweet {row['tweet_id']}"
        )
        print(row["text"][:120])


if __name__ == "__main__":
    main()