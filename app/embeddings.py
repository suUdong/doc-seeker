from sentence_transformers import SentenceTransformer
import logging
import time
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), '../logs/embeddings.log'), mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('embeddings')

# 모델 초기화 (처음 로딩 시 시간이 좀 걸림)
logger.info("SentenceTransformer 모델 로딩 시작")
start_time = time.time()
embedder = SentenceTransformer("all-MiniLM-L6-v2")
logger.info(f"모델 로딩 완료: {time.time() - start_time:.2f}초 소요")

def embed_text(text: str) -> list[float]:
    """SentenceTransformer 모델을 사용해 텍스트를 임베딩"""
    logger.debug(f"임베딩 생성 시작: {text[:50]}..." if len(text) > 50 else text)
    start_time = time.time()
    
    # 텍스트를 384차원 벡터로 변환
    embedding = embedder.encode(text, normalize_embeddings=True)
    
    elapsed_time = time.time() - start_time
    logger.info(f"임베딩 생성 완료: 길이 {len(text)}자, 차원 {len(embedding)}, 소요시간 {elapsed_time:.4f}초")
    
    return embedding.tolist()

def get_model_info() -> dict:
    """현재 사용 중인 모델 정보 반환"""
    model_info = {
        "model_name": embedder.get_model_name_or_path(),
        "dimension": embedder.get_sentence_embedding_dimension(),
        "max_seq_length": embedder.get_max_seq_length()
    }
    logger.info(f"모델 정보 요청: {model_info}")
    return model_info
