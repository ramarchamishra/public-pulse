from database.repositories.tweets_repository import get_unanalyzed_tweets
from database.repositories.sentiment_results_repository import (
    save_sentiment,
    get_sentiment_statistics,
)

from services.sentiment.roberta_sentiment import RobertaSentiment


class AnalysisService:

    def __init__(self):
        self.sentiment = RobertaSentiment()

    def analyze_tweets(self, limit: int = 100):

        tweets = get_unanalyzed_tweets(limit)

        analyzed_count = 0

        for tweet in tweets:

            label, confidence = self.sentiment.analyze(tweet)

            save_sentiment(
                tweet_id=tweet.tweet_id,
                model_name=self.sentiment.MODEL_NAME,
                label=label,
                confidence=confidence
            )

            analyzed_count += 1

        return {
            "tweets_found": len(tweets),
            "tweets_analyzed": analyzed_count
        }
    
    def get_search_summary(self, search_id: int):

        statistics = get_sentiment_statistics(search_id)

        summary = {
            "search_id": search_id,
            "total_tweets": 0,
            "positive": {
                "count": 0,
                "percentage": 0.0,
                "average_confidence": 0.0
            },
            "neutral": {
                "count": 0,
                "percentage": 0.0,
                "average_confidence": 0.0
            },
            "negative": {
                "count": 0,
                "percentage": 0.0,
                "average_confidence": 0.0
            }
        }

        for row in statistics:

            label = row["label"].lower()

            summary[label]["count"] = row["tweet_count"]
            summary[label]["average_confidence"] = round(
                row["average_confidence"], 4
            )

            summary["total_tweets"] += row["tweet_count"]

        total = summary["total_tweets"]

        if total > 0:

            for label in ("positive", "neutral", "negative"):

                summary[label]["percentage"] = round(
                    (summary[label]["count"] / total) * 100,
                    2
                )

        return summary