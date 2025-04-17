from sentence_transformers import SentenceTransformer

# 임베딩 모델 로드
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list[float]:
    """텍스트를 받아 벡터 리스트로 반환"""
    return embedder.encode(text).tolist()
