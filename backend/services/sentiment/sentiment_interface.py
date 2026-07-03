from abc import ABC, abstractmethod

from models.tweet import Tweet


class SentimentInterface(ABC):

    @abstractmethod
    def analyze(self, tweet: Tweet) -> tuple[str, float]:
        """
        Returns:
            (label, confidence)
        """
        pass