import pytest
import numpy as np
from app.embedding import ModelManager

class TestEmbedding:
    """임베딩 관련 테스트"""
    
    @pytest.fixture
    def model_manager(self):
        """테스트용 ModelManager 인스턴스"""
        return ModelManager()
    
    def test_model_loading(self, model_manager):
        """모델 로딩 테스트"""
        assert model_manager.model is not None, "모델이 로드되지 않았습니다."
        assert model_manager.tokenizer is not None, "토크나이저가 로드되지 않았습니다."
    
    def test_embedding_creation(self, model_manager):
        """텍스트 임베딩 생성 테스트"""
        test_text = "이것은 임베딩 테스트를 위한 텍스트입니다."
        embedding = model_manager.get_embeddings(test_text)
        
        # 임베딩 벡터 형태 확인
        assert isinstance(embedding, np.ndarray), "임베딩 결과가 numpy 배열이 아닙니다."
        assert embedding.ndim == 1, "임베딩 결과가 1차원 벡터가 아닙니다."
        assert embedding.shape[0] > 0, "임베딩 벡터 차원이 0입니다."
        
        # 임베딩 정규화 확인 (벡터 크기가 대략 1에 가까운지)
        vector_norm = np.linalg.norm(embedding)
        assert 0.9 <= vector_norm <= 1.1, f"벡터가 정규화되지 않았습니다. 현재 크기: {vector_norm}"
    
    def test_embedding_consistency(self, model_manager):
        """동일 텍스트의 임베딩 일관성 테스트"""
        test_text = "일관성 테스트를 위한 문장입니다."
        
        # 동일 텍스트에 대해 두 번 임베딩 생성
        embedding1 = model_manager.get_embeddings(test_text)
        embedding2 = model_manager.get_embeddings(test_text)
        
        # 두 임베딩 벡터가 동일한지 확인
        assert np.allclose(embedding1, embedding2, rtol=1e-5), "동일 텍스트에 대한 임베딩이 일관되지 않습니다."
    
    def test_similar_text_embeddings(self, model_manager):
        """의미적으로 유사한 텍스트의 임베딩 유사도 테스트"""
        text1 = "인공지능은 컴퓨터가 사람처럼 생각하고 학습하는 기술입니다."
        text2 = "AI는 기계가 인간의 사고 과정을 모방하는 기술입니다."
        text3 = "축구는 공을 발로 차는 스포츠입니다."
        
        emb1 = model_manager.get_embeddings(text1)
        emb2 = model_manager.get_embeddings(text2)
        emb3 = model_manager.get_embeddings(text3)
        
        # 코사인 유사도 계산 함수
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        # 유사한 텍스트(1과 2) 사이의 유사도는 높아야 함
        sim_1_2 = cosine_similarity(emb1, emb2)
        # 다른 텍스트(1과 3) 사이의 유사도는 낮아야 함
        sim_1_3 = cosine_similarity(emb1, emb3)
        
        assert sim_1_2 > sim_1_3, "의미적으로 유사한 텍스트의 임베딩 유사도가 기대와 다릅니다."
        assert sim_1_2 > 0.7, f"유사한 텍스트의 유사도가 너무 낮습니다: {sim_1_2}"
    
    def test_korean_text_handling(self, model_manager):
        """한글 텍스트 처리 테스트"""
        korean_text = "한글로 된 문장도 잘 처리되어야 합니다. 특수문자 !@#$%^&*()도 포함됩니다."
        
        embedding = model_manager.get_embeddings(korean_text)
        assert embedding is not None, "한글 텍스트 임베딩 생성 실패"
        assert embedding.shape[0] > 0, "한글 텍스트의 임베딩 벡터가 비어있습니다." 