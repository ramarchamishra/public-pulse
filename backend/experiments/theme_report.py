from services.themes.theme_analytics_service import ThemeAnalyticsService


SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"


def format_percentage(value):
    return "N/A" if value is None else f"{value:.1f}%"


def print_group(group):
    sentiment = group["sentiment"]

    print(
        f'{group["bertopic_topic_id"]:>5} '
        f'{group["tweet_count"]:>6} '
        f'{format_percentage(group["discussion_share_percentage"]):>8} '
        f'{format_percentage(sentiment["negative"]["percentage"]):>8} '
        f'{format_percentage(sentiment["neutral"]["percentage"]):>8} '
        f'{format_percentage(sentiment["positive"]["percentage"]):>8} '
        f'{format_percentage(sentiment["coverage_percentage"]):>8} '
        f'{group["name"]}'
    )

def print_theme_tweets(service, run_id, topic_id, limit=5):
    tweets = service.get_theme_tweets(
        run_id=run_id,
        bertopic_topic_id=topic_id,
        model_name=SENTIMENT_MODEL,
        limit=limit
    )

    if not tweets:
        print(f"\nNo tweets found for topic {topic_id}.")
        return

    print(f"\nRepresentative tweets for topic {topic_id}")
    print("=" * 100)

    for index, tweet in enumerate(tweets, start=1):
        theme_probability = tweet["theme_probability"]
        sentiment_confidence = tweet["sentiment_confidence"]

        theme_probability_text = (
            "N/A"
            if theme_probability is None
            else f"{theme_probability:.3f}"
        )

        sentiment_confidence_text = (
            "N/A"
            if sentiment_confidence is None
            else f"{sentiment_confidence:.3f}"
        )

        sentiment_label = tweet["sentiment_label"] or "N/A"

        print(
            f"\n{index}. Tweet ID: {tweet['tweet_id']}\n"
            f"Theme probability: {theme_probability_text}\n"
            f"Sentiment: {sentiment_label} "
            f"(confidence: {sentiment_confidence_text})\n"
            f"Text: {tweet['text']}"
        )

    print("\n" + "=" * 100)

def main():
    search_id = int(input("Enter search ID: "))
    service = ThemeAnalyticsService()

    summary = service.get_sentiment_summary_for_search(
        search_id=search_id,
        model_name=SENTIMENT_MODEL
    )

    if summary is None:
        print(f"No saved theme discovery run for search {search_id}.")
        return

    run = summary["run"]

    print(
        f'\nSearch {run["search_id"]} | Run {run["id"]} | '
        f'{summary["theme_count"]} themes | '
        f'{summary["tweet_count"]} tweets'
    )
    print("Pipeline:", run["pipeline_version"])
    print("Sentiment model:", summary["sentiment_model"])
    print("\nShare: percentage of all tweets assigned in this run.")
    print("Sentiment: percentages among analyzed tweets in each group.")
    print("Coverage: percentage of group tweets with sentiment results.\n")

    print(
        f'{"Topic":>5} {"Tweets":>6} {"Share":>8} '
        f'{"Neg":>8} {"Neutral":>8} {"Pos":>8} '
        f'{"Coverage":>8} Keywords'
    )
    print("-" * 120)

    for theme in summary["themes"]:
        print_group(theme)

    print("-" * 120)
    print_group(summary["noise"])

    groups = [*summary["themes"], summary["noise"]]
    analyzed_count = sum(
        group["sentiment"]["analyzed_count"] for group in groups
    )
    missing_count = sum(
        group["sentiment"]["missing_count"] for group in groups
    )

    print("\nAssignments with sentiment:", analyzed_count)
    print("Assignments missing sentiment:", missing_count)

    print(
        "\nEnter a topic ID to inspect representative tweets."
        "\nUse -1 for unclustered/noise tweets."
        "\nPress Enter to exit."
    )

    while True:
        value = input("\nTopic ID: ").strip()

        if value == "":
            break

        try:
            topic_id = int(value)
        except ValueError:
            print("Please enter a valid integer topic ID.")
            continue

        valid_topic_ids = {
            theme["bertopic_topic_id"]
            for theme in summary["themes"]
        }
        valid_topic_ids.add(-1)

        if topic_id not in valid_topic_ids:
            print("That topic does not exist in this run.")
            continue

        print_theme_tweets(
            service=service,
            run_id=run["id"],
            topic_id=topic_id,
            limit=5
        )


if __name__ == "__main__":
    main()