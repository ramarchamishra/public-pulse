from sentence_transformers import SentenceTransformer
import numpy as np
from utils.config import Config

from services.embeddings.embedding_interface import EmbeddingInterface


class SentenceTransformerEmbedding(EmbeddingInterface):
    """
    Generates sentence embeddings using a SentenceTransformer model.
    """

    MODEL_NAME = Config.EMBEDDING_MODEL

    _model = None

    def __init__(self):
        if SentenceTransformerEmbedding._model is None:
            print(f"Loading embedding model: {self.MODEL_NAME}")

            SentenceTransformerEmbedding._model = SentenceTransformer(
                self.MODEL_NAME
            )

    def encode(
        self,
        texts: list[str]
    ) -> np.ndarray:

        embeddings = SentenceTransformerEmbedding._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        return embeddings