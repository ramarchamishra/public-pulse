from database.repositories.theme_runs_repository import (
    get_latest_theme_run,
)
from database.repositories.themes_repository import (
    get_themes_for_run,
)
from database.repositories.theme_assignments_repository import (
    get_assignment_statistics_for_run,
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