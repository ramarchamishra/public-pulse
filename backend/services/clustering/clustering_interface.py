from abc import ABC, abstractmethod


class ClusteringInterface(ABC):

    @abstractmethod
    def discover_themes(self, texts, embeddings):
        """
        Discover discussion themes from text embeddings.

        Args:
            texts (list[str])
            embeddings (np.ndarray)

        Returns:
            tuple:
                topics
                probabilities
        """
        pass