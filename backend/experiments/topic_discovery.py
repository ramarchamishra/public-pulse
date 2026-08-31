import pandas as pd
import numpy as np
import os
from datetime import datetime

from database.repositories.tweets_repository import get_tweets_by_search
from services.embeddings.sentence_transformer_embedding import (
    SentenceTransformerEmbedding,
)
from services.clustering.bertopic_clusterer import BERTopicClusterer
from services.preprocessing.regex_text_cleaner import RegexTextCleaner


def main():
    search_id = int(input("Search ID:"))

    embedding_service = SentenceTransformerEmbedding()
    clusterer = BERTopicClusterer(embedding_model=embedding_service.model)

    tweets = get_tweets_by_search(search_id)
    texts = [tweet.text for tweet in tweets]
    cleaner = RegexTextCleaner()
    cleaned_texts = cleaner.clean_batch(texts)

    lines = []
    lines.append(f"Loaded {len(cleaned_texts)} tweets")
    print(f"Loaded {len(cleaned_texts)} tweets")

    embeddings = embedding_service.encode(cleaned_texts)
    lines.append("Embeddings generated")
    print("Embeddings generated")

    topics, probabilities = clusterer.discover_themes(
        cleaned_texts,
        embeddings,
    )

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.width", None)

    topic_info = clusterer.model.get_topic_info()

    lines.append("\n=== Full Topic Info ===\n")
    lines.append(topic_info.to_string())

    # --- Noise ratio ---
    n_total = len(topics)
    n_noise = sum(1 for t in topics if t == -1)
    lines.append("\n=== Noise Stats ===")
    lines.append(f"Total docs      : {n_total}")
    lines.append(f"Noise docs (-1) : {n_noise} ({n_noise / n_total:.1%})")
    lines.append(f"Clustered docs  : {n_total - n_noise} ({(n_total - n_noise) / n_total:.1%})")
    lines.append(
        f"Num real topics : {topic_info['Topic'].nunique() - (1 if -1 in topic_info['Topic'].values else 0)}"
    )

    # --- Per-topic keywords + representative docs ---
    lines.append("\n=== Per-Topic Detail ===")
    for topic_id in sorted(topic_info["Topic"].unique()):
        row = topic_info.loc[topic_info["Topic"] == topic_id].iloc[0]
        count = row["Count"]
        keywords = clusterer.model.get_topic(topic_id)

        lines.append(f"\n--- Topic {topic_id} (Count: {count}) ---")
        if keywords:
            kw_str = ", ".join(f"{word}({score:.3f})" for word, score in keywords)
            lines.append(f"Keywords: {kw_str}")

        reps = row.get("Representative_Docs", [])
        if isinstance(reps, (list, tuple)) and reps:
            lines.append("Representative docs:")
            for i, doc in enumerate(reps, 1):
                lines.append(f"  [{i}] {doc}")
        else:
            lines.append("Representative docs: (none found in topic_info)")

    # --- Probabilities summary (numpy-safe) ---
    if probabilities is not None:
        probs_arr = np.asarray(probabilities, dtype=float)
        lines.append("\n=== Probability Stats ===")
        lines.append(f"Shape : {probs_arr.shape}")
        if probs_arr.size:
            lines.append(f"Min   : {np.nanmin(probs_arr):.3f}")
            lines.append(f"Max   : {np.nanmax(probs_arr):.3f}")
            lines.append(f"Mean  : {np.nanmean(probs_arr):.3f}")
        else:
            lines.append("Empty probability array")
    else:
        lines.append("\nNo probabilities returned")

    # --- Write everything to a single txt report ---
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        output_dir, f"topic_analysis_search_{search_id}_{timestamp}.txt"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Optional: also dump the raw topic table as CSV for further analysis
    csv_path = os.path.join(
        output_dir, f"topic_info_search_{search_id}_{timestamp}.csv"
    )
    topic_info.to_csv(csv_path, index=False)

    print(f"Report written to {output_path}")
    print(f"Topic table (CSV) written to {csv_path}")


if __name__ == "__main__":
    main()