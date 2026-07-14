from services.embeddings.embedding_interface import EmbeddingInterface


class SentenceTransformerEmbedding(EmbeddingInterface):

    def encode(self, texts):
        raise NotImplementedError