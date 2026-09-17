import os
from datetime import datetime

import numpy as np
import pandas as pd

from database.connection import get_connection
from database.repositories.tweets_repository import get_tweets_by_search
from services.themes.theme_discovery_service import ThemeDiscoveryService
from utils.config import Config


def export_topic_assignments(
    tweets,
    original_texts,
    cleaned_texts,
    topics,
    output_path,
):
    if not (
        len(tweets)
        == len(original_texts)
        == len(cleaned_texts)
        == len(topics)
    ):
        raise ValueError(
            "Tweet/topic alignment mismatch: "
            f"tweets={len(tweets)}, "
            f"original_texts={len(original_texts)}, "
            f"cleaned_texts={len(cleaned_texts)}, "
            f"topics={len(topics)}"
        )

    rows = []

    for index, (tweet, original_text, cleaned_text, topic) in enumerate(
        zip(tweets, original_texts, cleaned_texts, topics)
    ):
        rows.append({
            "source_index": index,
            "tweet_id": tweet.tweet_id,
            "topic": int(topic),
            "original_text": original_text,
            "cleaned_text": cleaned_text,
        })

    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Topic assignments exported to: {output_path}")


def main():
    search_id = int(input("Enter search ID: "))

    if str(Config.DEVICE).split(":")[0].lower() != "cuda":
        raise RuntimeError("Configure CUDA before running discovery")

    service = ThemeDiscoveryService()
    result = service.discover_for_search(search_id)
    run_id = result["run_id"]

    print(f"\nSaved discovery run {run_id}:")
    print(result)

    # Reuse the fitted model for keyword and representative-doc reports.
    clusterer = service.clusterer

    # Read back the saved assignments for this exact run.
    connection = get_connection()

    try:
        assignment_rows = connection.execute("""
            SELECT
                tweet_id,
                bertopic_topic_id,
                probability
            FROM theme_assignments
            WHERE run_id = ?
        """, (run_id,)).fetchall()

    finally:
        connection.close()

    assignments_by_id = {
        str(row["tweet_id"]): row
        for row in assignment_rows
    }

    tweets = get_tweets_by_search(search_id)

    if {str(tweet.tweet_id) for tweet in tweets} != set(assignments_by_id):
        raise RuntimeError(
            "Search tweets differ from the saved run assignments"
        )

    texts = [tweet.text for tweet in tweets]
    cleaned_texts = service.cleaner.clean_batch(texts)

    # Match by tweet ID instead of assuming database row ordering.
    topics = [
        assignments_by_id[str(tweet.tweet_id)]["bertopic_topic_id"]
        for tweet in tweets
    ]

    probabilities = [
        row["probability"]
        for row in assignment_rows
        if row["probability"] is not None
    ]

    lines = [
        f"Search ID: {search_id}",
        f"Discovery run ID: {run_id}",
        f"Pipeline version: {service.PIPELINE_VERSION}",
        f"Loaded {len(tweets)} tweets",
    ]

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.width", None)

    topic_info = clusterer.model.get_topic_info()

    lines.append("\n=== Full Topic Info ===\n")
    lines.append(topic_info.to_string())

    # Noise and clustered counts from persisted assignments.
    n_total = len(topics)
    n_noise = sum(1 for topic in topics if topic == -1)
    n_clustered = n_total - n_noise
    n_real_topics = len({topic for topic in topics if topic != -1})

    lines.append("\n=== Noise Stats ===")
    lines.append(f"Total docs      : {n_total}")
    lines.append(
        f"Noise docs (-1) : {n_noise} ({n_noise / n_total:.1%})"
    )
    lines.append(
        f"Clustered docs  : {n_clustered} ({n_clustered / n_total:.1%})"
    )
    lines.append(f"Num real topics : {n_real_topics}")

    # Per-topic keywords and BERTopic representative documents.
    lines.append("\n=== Per-Topic Detail ===")

    for topic_id in sorted(topic_info["Topic"].unique()):
        row = topic_info.loc[topic_info["Topic"] == topic_id].iloc[0]
        count = row["Count"]
        keywords = clusterer.model.get_topic(topic_id)

        lines.append(f"\n--- Topic {topic_id} (Count: {count}) ---")

        if keywords:
            kw_str = ", ".join(
                f"{word}({score:.3f})"
                for word, score in keywords
            )
            lines.append(f"Keywords: {kw_str}")

        reps = row.get("Representative_Docs", [])

        if isinstance(reps, (list, tuple)) and reps:
            lines.append("Representative docs:")
            for index, doc in enumerate(reps, start=1):
                lines.append(f"  [{index}] {doc}")
        else:
            lines.append("Representative docs: (none found in topic_info)")

    # Summarize saved membership scores, excluding NULL values.
    probs_arr = np.asarray(probabilities, dtype=float)
    lines.append(
        "\n=== Stored Assignment Probability Stats "
        "(non-null values only) ==="
    )
    lines.append(f"Shape : {probs_arr.shape}")

    if probs_arr.size:
        lines.append(f"Min   : {np.nanmin(probs_arr):.3f}")
        lines.append(f"Max   : {np.nanmax(probs_arr):.3f}")
        lines.append(f"Mean  : {np.nanmean(probs_arr):.3f}")
    else:
        lines.append("No non-null assignment probabilities")

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = (
        f"run_{run_id}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    )

    output_path = os.path.join(
        output_dir,
        f"topic_analysis_search_{search_id}_{timestamp}.txt",
    )

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    csv_path = os.path.join(
        output_dir,
        f"topic_info_search_{search_id}_{timestamp}.csv",
    )
    topic_info.to_csv(csv_path, index=False)

    assignments_path = os.path.join(
        output_dir,
        f"topic_assignments_search_{search_id}_{timestamp}.csv",
    )

    export_topic_assignments(
        tweets=tweets,
        original_texts=texts,
        cleaned_texts=cleaned_texts,
        topics=topics,
        output_path=assignments_path,
    )

    print(f"Report written to {output_path}")
    print(f"Topic table (CSV) written to {csv_path}")
    print(f"Topic assignments (CSV) written to {assignments_path}")


if __name__ == "__main__":
    main()