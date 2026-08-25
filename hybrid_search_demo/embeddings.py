"""
Module xử lý tạo Dense Vectors (Nomic MoE v2) và Sparse Vectors (BM25).
"""
import logging
from typing import List, Tuple
from fastembed import SparseTextEmbedding
from qdrant_client import models
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger(__name__)


class DenseEmbeddingService:
    """Service chịu trách nhiệm trích xuất Dense Vector từ mô hình Nomic MoE v2."""

    def __init__(self, model_name: str = settings.dense_model_name) -> None:
        logger.info(f"Đang khởi tạo mô hình Dense Embedding: {model_name}...")
        try:
            self.model = SentenceTransformer(model_name, trust_remote_code=True)
            logger.info("Khởi tạo Dense Model thành công.")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Dense Model: {e}")
            raise e

    def encode_documents(self, documents: List[str]) -> List[List[float]]:
        """Mã hóa danh sách văn bản thành danh sách dense vectors với prefix search_document:"""
        prefixed_docs = [f"{settings.prefix_document}{doc}" for doc in documents]
        embeddings = self.model.encode(prefixed_docs, convert_to_numpy=True)
        return embeddings.tolist()

    def encode_query(self, query: str) -> List[float]:
        """Mã hóa câu truy vấn thành dense vector với prefix search_query:"""
        prefixed_query = f"{settings.prefix_query}{query}"
        embedding = self.model.encode(prefixed_query, convert_to_numpy=True)
        return embedding.tolist()


class SparseEmbeddingService:
    """Service chịu trách nhiệm trích xuất Sparse Vector (BM25) qua FastEmbed."""

    def __init__(self, model_name: str = settings.sparse_model_name) -> None:
        logger.info(f"Đang khởi tạo mô hình Sparse BM25 Embedding: {model_name}...")
        try:
            self.model = SparseTextEmbedding(model_name=model_name)
            logger.info("Khởi tạo Sparse BM25 Model thành công.")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Sparse BM25 Model: {e}")
            raise e

    def encode_documents(self, documents: List[str]) -> List[models.SparseVector]:
        """Mã hóa danh sách văn bản thành các đối tượng SparseVector của Qdrant."""
        sparse_embeddings = list(self.model.embed(documents))
        result: List[models.SparseVector] = []
        for emb in sparse_embeddings:
            result.append(
                models.SparseVector(
                    indices=emb.indices.tolist(),
                    values=emb.values.tolist()
                )
            )
        return result

    def encode_query(self, query: str) -> models.SparseVector:
        """Mã hóa câu truy vấn thành đối tượng SparseVector của Qdrant."""
        sparse_embeddings = list(self.model.embed([query]))
        emb = sparse_embeddings[0]
        return models.SparseVector(
            indices=emb.indices.tolist(),
            values=emb.values.tolist()
        )
