from sentence_transformers import SentenceTransformer

# # 모델 초기화 (처음 로딩 시 시간이 좀 걸림)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list[float]:
    """SentenceTransformer 모델을 사용해 텍스트를 임베딩"""
    # 텍스트를 384차원 벡터로 변환
    embedding = embedder.encode(text, normalize_embeddings=True)
    return embedding.tolist()
