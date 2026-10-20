from database.repositories.tweets_repository import (
    get_tweets_by_search,
)
from services.preprocessing.regex_text_cleaner import RegexTextCleaner
from services.embeddings.sentence_transformer_embedding import (
    SentenceTransformerEmbedding,
)
from services.clustering.bertopic_clusterer import BERTopicClusterer
import re
from database.repositories.searches_repository import get_search_topic


class SearchComparisonService:

    MIN_SIZE_RATIO = 0.5

    def prepare_comparison(
        self,
        search_id_a: int,
        search_id_b: int,
        exclude_explicit_ads: bool = False
    ) -> dict:

        if search_id_a == search_id_b:
            raise ValueError(
                "Comparison requires two different search IDs"
            )

        tweets_a = get_tweets_by_search(search_id_a)
        tweets_b = get_tweets_by_search(search_id_b)


        original_count_a = len(tweets_a)
        original_count_b = len(tweets_b)

        if exclude_explicit_ads:
            tweets_a = [
                tweet for tweet in tweets_a
                if not self.is_explicit_ad(tweet.text)
            ]

            tweets_b = [
                tweet for tweet in tweets_b
                if not self.is_explicit_ad(tweet.text)
            ]

        excluded_ads_a = original_count_a - len(tweets_a)
        excluded_ads_b = original_count_b - len(tweets_b)


        if not tweets_a:
            raise ValueError(
                f"No tweets found for search ID {search_id_a}"
            )

        if not tweets_b:
            raise ValueError(
                f"No tweets found for search ID {search_id_b}"
            )

        count_a = len(tweets_a)
        count_b = len(tweets_b)

        smaller_count = min(count_a, count_b)
        larger_count = max(count_a, count_b)

        size_ratio = smaller_count / larger_count

        if size_ratio < self.MIN_SIZE_RATIO:
            raise ValueError(
                "Search sizes are too imbalanced for comparison: "
                f"{count_a} vs {count_b} tweets. "
                "The smaller search must contain at least "
                "50% as many tweets as the larger search."
            )

        tweet_membership = {}

        for tweet in tweets_a:
            tweet_membership.setdefault(
                tweet.tweet_id,
                {
                    "tweet": tweet,
                    "search_ids": set(),
                }
            )

            tweet_membership[
                tweet.tweet_id
            ]["search_ids"].add(search_id_a)

        for tweet in tweets_b:
            tweet_membership.setdefault(
                tweet.tweet_id,
                {
                    "tweet": tweet,
                    "search_ids": set(),
                }
            )

            tweet_membership[
                tweet.tweet_id
            ]["search_ids"].add(search_id_b)

        unique_tweets = [
            item["tweet"]
            for item in tweet_membership.values()
        ]

        overlap_count = sum(
            1
            for item in tweet_membership.values()
            if len(item["search_ids"]) == 2
        )

        return {
            "search_id_a": search_id_a,
            "search_id_b": search_id_b,
            "tweet_count_a": count_a,
            "tweet_count_b": count_b,
            "size_ratio": size_ratio,
            "unique_tweet_count": len(unique_tweets),
            "overlap_count": overlap_count,
            "tweets": unique_tweets,
            "tweet_membership": tweet_membership,
            "excluded_ads_a": excluded_ads_a,
            "excluded_ads_b": excluded_ads_b,
        }


    
    def discover_shared_themes(
        self,
        search_id_a: int,
        search_id_b: int,
        exclude_explicit_ads: bool = False
    ) -> dict:

        comparison = self.prepare_comparison(
            search_id_a,
            search_id_b,
            exclude_explicit_ads=exclude_explicit_ads
        )

    
        tweets = comparison["tweets"]
    
        original_texts = [
            tweet.text for tweet in tweets
        ]
    
        cleaner = RegexTextCleaner()
        embedding_service = SentenceTransformerEmbedding()
    
        cleaned_texts = cleaner.clean_batch(original_texts)

        search_topics = (
            get_search_topic(search_id_a),
            get_search_topic(search_id_b),
        )

        if not all(search_topics):
            raise ValueError("Could not retrieve both search topics")

        normalized_texts = self.normalize_subject_texts(
            cleaned_texts,
            search_topics
        )

        embeddings = embedding_service.encode(normalized_texts)
    
        clusterer = BERTopicClusterer(
            embedding_model=embedding_service.model
        )
    
        discovered_topics, _ = clusterer.discover_themes(
            normalized_texts,
            embeddings
        )
    
        topics = [
            int(topic) for topic in discovered_topics
        ]
    
        if len(topics) != len(tweets):
            raise RuntimeError(
                "Tweet/topic alignment mismatch"
            )
    
        topic_ids = sorted(
            set(topics) - {-1}
        )
    
        noise_count = topics.count(-1)
    
        return {
            "tweet_search_ids": {
                tweet_id: item["search_ids"]
                for tweet_id, item in comparison["tweet_membership"].items()
            },
            "search_id_a": search_id_a,
            "search_id_b": search_id_b,
            "tweet_count_a": comparison["tweet_count_a"],
            "tweet_count_b": comparison["tweet_count_b"],
            "unique_tweet_count": len(tweets),
            "theme_count": len(topic_ids),
            "clustered_count": len(tweets) - noise_count,
            "noise_count": noise_count,
            "topic_assignments": dict(
                zip(
                    [tweet.tweet_id for tweet in tweets],
                    topics
                )
            ),
            "model": clusterer.model,
        }

    def summarize_joint_themes(self, discovery: dict) -> dict:
        search_a = discovery["search_id_a"]
        search_b = discovery["search_id_b"]
    
        counts = {}
    
        for tweet_id, topic_id in discovery["topic_assignments"].items():
            topic_counts = counts.setdefault(
                topic_id,
                {search_a: 0, search_b: 0}
            )
    
            for search_id in discovery["tweet_search_ids"][tweet_id]:
                topic_counts[search_id] += 1
    
        themes = []
    
        for topic_id, topic_counts in sorted(counts.items()):
            count_a = topic_counts[search_a]
            count_b = topic_counts[search_b]
    
            keywords = (
                []
                if topic_id == -1
                else [
                    word
                    for word, _ in (
                        discovery["model"].get_topic(topic_id) or []
                    )[:4]
                ]
            )
    
            themes.append({
                "topic_id": topic_id,
                "keywords": keywords,
                "count_a": count_a,
                "count_b": count_b,
                "share_a": (
                    count_a / discovery["tweet_count_a"] * 100
                ),
                "share_b": (
                    count_b / discovery["tweet_count_b"] * 100
                ),
                "is_shared": (
                    topic_id != -1
                    and count_a > 0
                    and count_b > 0
                ),
            })
    
        total_a = sum(t["count_a"] for t in themes)
        total_b = sum(t["count_b"] for t in themes)
    
        if (
            total_a != discovery["tweet_count_a"]
            or total_b != discovery["tweet_count_b"]
        ):
            raise RuntimeError(
                "Per-search topic counts do not match input counts"
            )
    
        return {
            "search_id_a": search_a,
            "search_id_b": search_b,
            "themes": themes,
        }

    @staticmethod
    def normalize_subject_texts(
        texts: list[str],
        search_topics: tuple[str, str]
    ) -> list[str]:

        patterns = []

        for topic in sorted(search_topics, key=len, reverse=True):

            tokens = re.findall(r"[A-Za-z]+|\d+", topic)

            if not tokens:
                raise ValueError(
                    f"Invalid search topic: {topic!r}"
                )

            pattern = re.compile(
                r"(?<!\w)"
                + r"[\s_-]*".join(map(re.escape, tokens))
                + r"(?!\w)",
                flags=re.IGNORECASE
            )

            patterns.append(pattern)

        normalized_texts = []

        for text in texts:
            normalized = text

            for pattern in patterns:
                normalized = pattern.sub(
                    "SUBJECT",
                    normalized
                )

            normalized_texts.append(normalized)

        return normalized_texts

    
    @staticmethod
    def is_explicit_ad(text: str) -> bool:
        return re.search(
            r"(?<!\w)#ad\b",
            text or "",
            flags=re.IGNORECASE
        ) is not None
