from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
from hdbscan import HDBSCAN

from services.clustering.clustering_interface import ClusteringInterface


class BERTopicClusterer(ClusteringInterface):

    def __init__(
        self,
        embedding_model=None,
        min_cluster_size=12,
        min_samples=5,
        cluster_selection_method="eom",
        calculate_probabilities=True,
    ):
        self.umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            random_state=42,
        )

        self.hdbscan_model = HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method=cluster_selection_method,
            prediction_data=True,
        )

        self.vectorizer_model = CountVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
        )

        self.ctfidf_model = ClassTfidfTransformer(
            reduce_frequent_words=True
        )

        self.model = BERTopic(
            embedding_model=embedding_model,
            umap_model=self.umap_model,
            hdbscan_model=self.hdbscan_model,
            vectorizer_model=self.vectorizer_model,
            ctfidf_model=self.ctfidf_model,
            calculate_probabilities=calculate_probabilities,
            verbose=True,
        )

    def discover_themes(self, texts, embeddings):
        return self.model.fit_transform(
            texts,
            embeddings
        )