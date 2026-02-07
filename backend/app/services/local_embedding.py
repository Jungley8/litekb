"""
本地嵌入计算服务
"""

from typing import List, Dict, Optional
from loguru import logger
from sentence_transformers import SentenceTransformer


class LocalEmbedding:
    """本地嵌入模型"""

    SUPPORTED_MODELS = {
        "BAAI/bge-large-zh": 1024,
        "BAAI/bge-base-zh": 768,
        "BAAI/bge-small-zh": 512,
        "shibing624/text2vec-base-chinese": 768,
        "GanymedeNil/text2vec-large-chinese": 1024,
    }

    def __init__(
        self,
        model_name: str = "BAAI/bge-large-zh",
        device: str = "cpu",
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self._model = None

    @property
    def model(self):
        """懒加载模型"""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        return self.SUPPORTED_MODELS.get(self.model_name, 768)

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> List[List[float]]:
        """编码文本为向量"""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=self.normalize,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding encode failed: {e}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        return self.encode([text], batch_size=1)[0]

    def encode_query(self, query: str) -> List[float]:
        """编码查询 (BGE 需要加 query 前缀)"""
        prefixed_query = f"为检索任务生成表示: {query}"
        return self.encode_single(prefixed_query)


# 全局实例
_local_embedding: Optional[LocalEmbedding] = None


def get_embedding_model(
    model_name: str = None,
    use_local: bool = False,
) -> "LocalEmbedding":
    """获取嵌入模型"""
    global _local_embedding

    if _local_embedding is None:
        model = model_name or "BAAI/bge-large-zh"
        _local_embedding = LocalEmbedding(model_name=model)

    return _local_embedding


async def compute_embeddings(
    texts: List[str],
    model_name: str = None,
    use_api: bool = True,
) -> List[List[float]]:
    """计算嵌入向量 (API 或本地)"""
    if use_api:
        # 使用 OpenAI Embedding API
        from app.services.vector import embedding_api

        return await embedding_api.embed_texts(texts)
    else:
        # 使用本地模型
        model = get_embedding_model(model_name)
        return model.encode(texts)
