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


if __name__ == "__main__":
    main()