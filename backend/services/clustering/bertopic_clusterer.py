from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from bertopic.representation import KeyBERTInspired
from sklearn.feature_extraction.text import CountVectorizer
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
            random_state=42,
        )

        hdbscan_model = HDBSCAN(
            min_cluster_size=15,   # — pushes tiny near-duplicate clusters to merge or fall to outliers
            min_samples=5,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        # kills the stopword leakage
        vectorizer_model = CountVectorizer(
            stop_words="english",
            ngram_range=(1, 2),      
            min_df=2,
        )

        # NEW: down-weights words that are frequent across MANY topics 
        # appear everywhere in this dataset and currently drown out the distinctive terms)
        ctfidf_model = ClassTfidfTransformer(reduce_frequent_words=True)

        # NEW: reranks keywords by semantic similarity to the topic centroid instead of raw c-TF-IDF rank
        representation_model = KeyBERTInspired()
        self.vectorizer_model = vectorizer_model

        self.model = BERTopic(
            embedding_model=Config.EMBEDDING_MODEL,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            ctfidf_model=ctfidf_model,
            representation_model=representation_model,
            calculate_probabilities=True,
            verbose=True,
        )

    def discover_themes(self, texts, embeddings):
        topics, probabilities = self.model.fit_transform(texts, embeddings)

        # NEW: reassigns outlier docs (-1) using c-TF-IDF similarity to existing topics
        topics = self.model.reduce_outliers(
            texts, topics, strategy="c-tf-idf", threshold=0.1
        )
        self.model.update_topics(texts, topics=topics, vectorizer_model=self.vectorizer_model)

        return topics, probabilities