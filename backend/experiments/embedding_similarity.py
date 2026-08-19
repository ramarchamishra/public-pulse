from sklearn.metrics.pairwise import cosine_similarity

from services.embeddings.sentence_transformer_embedding import (
    SentenceTransformerEmbedding,
)

embedding_service = SentenceTransformerEmbedding()

texts = [
    "The camera is amazing.",
    "Night photography is fantastic.",
    "Battery drains too quickly.",
    "This cookie is tasty.",
]

embeddings = embedding_service.encode(texts)

pairs = [
    (0, 1),
    (0, 2),
    (2, 3),
]

for i, j in pairs:
    score = cosine_similarity(
        [embeddings[i]],
        [embeddings[j]]
    )[0][0]

    print("=" * 60)
    print(texts[i])
    print(texts[j])
    print(f"Similarity: {score:.4f}")