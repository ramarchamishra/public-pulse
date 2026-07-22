from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN

from utils.config import Config
from services.clustering.clustering_interface import ClusteringInterface


class BERTopicClusterer(ClusteringInterface):

    def __init__(self):
        umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            random_state=42,  # <-- pins the reduction, makes runs reproducible
        )

        hdbscan_model = HDBSCAN(
            min_cluster_size=10,   # tune this: lower = more, smaller topics; higher = fewer, bigger topics
            min_samples=5,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        self.model = BERTopic(
            embedding_model=None,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
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