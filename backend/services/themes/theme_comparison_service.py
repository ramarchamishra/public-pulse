from database.repositories.theme_runs_repository import (
    get_latest_theme_run,
)
from database.repositories.themes_repository import (
    get_themes_for_run,
)
from database.repositories.theme_assignments_repository import (
    get_theme_tweet_texts_for_run,
)


class ThemeComparisonService:

    def get_theme_text_groups_for_search(
        self,
        search_id: int
    ) -> dict | None:

        run = get_latest_theme_run(search_id)

        if run is None:
            return None

        run_id = run["id"]

        themes = get_themes_for_run(run_id)
        rows = get_theme_tweet_texts_for_run(run_id)

        texts_by_theme_id = {}

        for row in rows:
            theme_id = row["theme_id"]

            texts_by_theme_id.setdefault(
                theme_id,
                []
            ).append(row["text"])

        grouped_themes = []

        for theme in themes:
            grouped_themes.append({
                "theme_id": theme["id"],
                "bertopic_topic_id": theme["bertopic_topic_id"],
                "name": theme["name"],
                "keywords": theme["keywords"],
                "tweet_count": theme["tweet_count"],
                "texts": texts_by_theme_id.get(
                    theme["id"],
                    []
                ),
            })

        return {
            "run": dict(run),
            "themes": grouped_themes,
        }