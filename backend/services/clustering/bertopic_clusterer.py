from bertopic import BERTopic
from utils.config import Config
from services.clustering.clustering_interface import ClusteringInterface


class BERTopicClusterer(ClusteringInterface):

    def __init__(self):
        self.model = BERTopic(
            embedding_model=None,
            calculate_probabilities=True,
            verbose=True,
        )

    def discover_themes(self, texts, embeddings):
        """
        Discover themes using precomputed embeddings.

        Args:
            texts (list[str])
            embeddings (np.ndarray)

        Returns:
            topics, probabilities
        """
        topics, probabilities = self.model.fit_transform(
            texts,
            embeddings,
        )

        return topics, probabilities