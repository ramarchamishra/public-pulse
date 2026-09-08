import math

from database.connection import get_connection
from database.repositories.tweets_repository import get_tweets_by_search
from database.repositories.theme_runs_repository import create_theme_run
from database.repositories.themes_repository import create_theme
from database.repositories.theme_assignments_repository import (
    create_theme_assignments,
)

from services.preprocessing.regex_text_cleaner import RegexTextCleaner
from services.embeddings.sentence_transformer_embedding import (
    SentenceTransformerEmbedding,
)
from services.clustering.bertopic_clusterer import BERTopicClusterer


class ThemeDiscoveryService:

    PIPELINE_VERSION = "m3_v1"

    def __init__(self):
        self.cleaner = RegexTextCleaner()
        self.embedding_service = SentenceTransformerEmbedding()

        self.clusterer = BERTopicClusterer(
            embedding_model=self.embedding_service.model
        )

    def discover_for_search(self, search_id: int) -> dict:
        tweets = get_tweets_by_search(search_id)

        if not tweets:
            raise ValueError(
                f"No tweets found for search ID {search_id}"
            )

        original_texts = [tweet.text for tweet in tweets]
        cleaned_texts = self.cleaner.clean_batch(original_texts)

        embeddings = self.embedding_service.encode(cleaned_texts)

        discovered_topics, _ = self.clusterer.discover_themes(
            cleaned_texts,
            embeddings
        )

        topics = [int(topic) for topic in discovered_topics]

        if len(tweets) != len(topics):
            raise RuntimeError(
                "Tweet/topic alignment mismatch: "
                f"tweets={len(tweets)}, topics={len(topics)}"
            )

        probabilities = self._get_assignment_probabilities(
            cleaned_texts,
            topics
        )

        real_topic_ids = sorted({
            topic_id
            for topic_id in topics
            if topic_id != -1
        })

        theme_data = {}

        for topic_id in real_topic_ids:
            raw_keywords = (
                self.clusterer.model.get_topic(topic_id) or []
            )

            keywords = [
                (str(word), float(score))
                for word, score in raw_keywords
            ]

            theme_data[topic_id] = {
                "name": self._build_theme_name(
                    topic_id,
                    keywords
                ),
                "keywords": keywords,
            }

        connection = get_connection()

        try:
            run_id = create_theme_run(
                connection=connection,
                search_id=search_id,
                embedding_model=self.embedding_service.MODEL_NAME,
                pipeline_version=self.PIPELINE_VERSION
            )

            database_theme_ids = {}

            for topic_id, data in theme_data.items():
                database_theme_ids[topic_id] = create_theme(
                    connection=connection,
                    run_id=run_id,
                    bertopic_topic_id=topic_id,
                    name=data["name"],
                    keywords=data["keywords"]
                )

            assignments = []

            for tweet, topic_id, probability in zip(
                tweets,
                topics,
                probabilities
            ):
                theme_id = (
                    None
                    if topic_id == -1
                    else database_theme_ids[topic_id]
                )

                assignments.append((
                    tweet.tweet_id,
                    theme_id,
                    topic_id,
                    probability
                ))

            create_theme_assignments(
                connection=connection,
                run_id=run_id,
                assignments=assignments
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

        noise_count = sum(
            1 for topic_id in topics if topic_id == -1
        )

        return {
            "run_id": run_id,
            "search_id": search_id,
            "tweet_count": len(tweets),
            "theme_count": len(real_topic_ids),
            "clustered_count": len(tweets) - noise_count,
            "noise_count": noise_count,
        }

    def _get_assignment_probabilities(
        self,
        cleaned_texts: list[str],
        topics: list[int]
    ) -> list[float | None]:
        document_info = self.clusterer.model.get_document_info(
            cleaned_texts
        )

        document_topics = [
            int(topic)
            for topic in document_info["Topic"].tolist()
        ]

        if document_topics != topics:
            raise RuntimeError(
                "BERTopic document ordering changed unexpectedly"
            )

        if "Probability" not in document_info.columns:
            return [None] * len(topics)

        probabilities = []

        for topic_id, value in zip(
            topics,
            document_info["Probability"].tolist()
        ):
            if topic_id == -1 or value is None:
                probabilities.append(None)
                continue

            probability = float(value)

            if not math.isfinite(probability):
                probabilities.append(None)
                continue

            if not 0.0 <= probability <= 1.0:
                raise RuntimeError(
                    f"Invalid topic probability: {probability}"
                )

            probabilities.append(probability)

        return probabilities

    @staticmethod
    def _build_theme_name(
        topic_id: int,
        keywords: list[tuple[str, float]]
    ) -> str:
        top_words = [
            word for word, _ in keywords[:4]
        ]

        if not top_words:
            return f"Theme {topic_id}"

        return ", ".join(top_words)