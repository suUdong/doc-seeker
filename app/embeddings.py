# from sentence_transformers import SentenceTransformer
import numpy as np
import hashlib

# 실제 임베딩 대신 임시 임베딩 함수 사용
# embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> list[float]:
    """임시 임베딩 함수: 텍스트 해시를 기반으로 임베딩 생성"""
    # 개발 중 임시로 사용할 간단한 임베딩 함수
    # 해시 기반 벡터 생성 (실제 의미 임베딩은 아님)
    text_hash = hashlib.md5(text.encode()).hexdigest()
    hash_int = [int(c, 16) for c in text_hash]
    
    # 384차원 벡터로 확장 (all-MiniLM-L6-v2 모델과 동일한 차원)
    vec = []
    for i in range(384):
        # 해시값을 순환하며 -1과 1 사이의 값 생성
        vec.append((hash_int[i % len(hash_int)] / 8.0) - 1.0)
    
    # 단위 벡터로 정규화
    vec_norm = np.array(vec) / np.linalg.norm(vec)
    return vec_norm.tolist()
