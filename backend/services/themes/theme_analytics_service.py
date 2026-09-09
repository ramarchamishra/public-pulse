from database.repositories.theme_runs_repository import (
    get_latest_theme_run,
)
from database.repositories.themes_repository import (
    get_themes_for_run,
)
from database.repositories.theme_assignments_repository import (
    get_assignment_statistics_for_run,
    get_theme_sentiment_statistics_for_run,
    get_tweets_for_theme
)

class ThemeAnalyticsService:

    def get_summary_for_search(
        self,
        search_id: int
    ) -> dict | None:
        run = get_latest_theme_run(search_id)

        if run is None:
            return None

        run_id = run["id"]

        themes = get_themes_for_run(run_id)
        statistics = get_assignment_statistics_for_run(run_id)

        total_count = statistics["total_count"]
        clustered_count = statistics["clustered_count"]
        noise_count = statistics["noise_count"]

        clustered_percentage = (
            clustered_count / total_count * 100
            if total_count else 0.0
        )

        noise_percentage = (
            noise_count / total_count * 100
            if total_count else 0.0
        )

        return {
            "run": dict(run),
            "tweet_count": total_count,
            "theme_count": len(themes),
            "clustered_count": clustered_count,
            "noise_count": noise_count,
            "clustered_percentage": clustered_percentage,
            "noise_percentage": noise_percentage,
            "average_probability": statistics["average_probability"],
            "themes": themes,
        }

    def get_sentiment_summary_for_search(
        self,
        search_id: int,
        model_name: str
    ) -> dict | None:
        summary = self.get_summary_for_search(search_id)

        if summary is None:
            return None

        rows = get_theme_sentiment_statistics_for_run(
            summary["run"]["id"],
            model_name
        )

        rows_by_topic = {}

        for row in rows:
            topic_id = row["bertopic_topic_id"]
            rows_by_topic.setdefault(topic_id, []).append(row)

        noise = {
            "bertopic_topic_id": -1,
            "name": "Unclustered tweets",
            "tweet_count": summary["noise_count"],
        }

        for group in [*summary["themes"], noise]:
            topic_id = group["bertopic_topic_id"]
            total_count = group["tweet_count"]

            sentiment = {
                label: {
                    "count": 0,
                    "percentage": None,
                    "average_confidence": None,
                }
                for label in ("positive", "neutral", "negative")
            }

            analyzed_count = 0

            for row in rows_by_topic.get(topic_id, []):
                if row["label"] is None:
                    continue

                label = row["label"].lower()

                if label not in sentiment:
                    raise ValueError(
                        f"Unexpected sentiment label: {row['label']}"
                    )

                count = row["tweet_count"]
                analyzed_count += count

                sentiment[label]["count"] = count
                sentiment[label]["average_confidence"] = (
                    row["average_confidence"]
                )

            if analyzed_count:
                for label in ("positive", "neutral", "negative"):
                    sentiment[label]["percentage"] = (
                        sentiment[label]["count"]
                        / analyzed_count * 100
                    )

            group["sentiment"] = {
                "analyzed_count": analyzed_count,
                "missing_count": total_count - analyzed_count,
                "coverage_percentage": (
                    analyzed_count / total_count * 100
                    if total_count else None
                ),
                **sentiment,
            }

        summary["sentiment_model"] = model_name
        summary["noise"] = noise

        return summary

    def get_theme_tweets(
        self,
        run_id: int,
        bertopic_topic_id: int,
        model_name: str,
        limit: int = 5
    ) -> list[dict]:
        return get_tweets_for_theme(
            run_id=run_id,
            bertopic_topic_id=bertopic_topic_id,
            model_name=model_name,
            limit=limit
        )