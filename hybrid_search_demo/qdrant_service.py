"""
Module quản lý kết nối Qdrant, khởi tạo Collection và thực hiện Hybrid Search RRF.
"""
import logging
from typing import Any, Dict, List
from qdrant_client import QdrantClient, models

from config import settings

logger = logging.getLogger(__name__)


class QdrantHybridService:
    """Service thao tác trực tiếp với Qdrant Vector Engine."""

    def __init__(self, location: str = ":memory:") -> None:
        """Khởi tạo Qdrant Client (Mặc định chạy In-Memory cho môi trường thử nghiệm)."""
        logger.info(f"Kết nối tới Qdrant Vector Engine tại: {location}...")
        self.client = QdrantClient(location=location)

    def init_collection(self) -> None:
        """Khởi tạo hoặc làm mới Collection hỗ trợ Dual-Vector (Dense + Sparse BM25)."""
        logger.info(f"Đang thiết lập Collection '{settings.collection_name}'...")
        
        # Nếu collection đã tồn tại thì xóa làm mới
        if self.client.collection_exists(collection_name=settings.collection_name):
            self.client.delete_collection(collection_name=settings.collection_name)

        self.client.create_collection(
            collection_name=settings.collection_name,
            vectors_config={
                settings.dense_vector_name: models.VectorParams(
                    size=settings.dense_vector_size,
                    distance=models.Distance.COSINE
                )
            },
            sparse_vectors_config={
                settings.sparse_vector_name: models.SparseVectorParams(
                    index=models.SparseIndexParams(on_disk=False)
                )
            }
        )
        logger.info(f"Khởi tạo thành công Collection '{settings.collection_name}'.")

    def upsert_documents(
        self,
        texts: List[str],
        dense_vectors: List[List[float]],
        sparse_vectors: List[models.SparseVector],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Đưa danh sách tài liệu cùng các vector tương ứng vào Qdrant."""
        logger.info(f"Đang index {len(texts)} tài liệu vào Qdrant...")
        points: List[models.PointStruct] = []

        for idx, (text, dense_vec, sparse_vec, meta) in enumerate(
            zip(texts, dense_vectors, sparse_vectors, metadatas), start=1
        ):
            payload = {"text": text, **meta}
            points.append(
                models.PointStruct(
                    id=idx,
                    vector={
                        settings.dense_vector_name: dense_vec,
                        settings.sparse_vector_name: sparse_vec
                    },
                    payload=payload
                )
            )

        self.client.upsert(
            collection_name=settings.collection_name,
            points=points
        )
        logger.info(f"Đã index thành công {len(points)} points vào collection.")

    def search_hybrid_rrf(
        self,
        query_dense: List[float],
        query_sparse: models.SparseVector,
        top_k: int = settings.top_k_final
    ) -> List[Dict[str, Any]]:
        """Thực thi truy vấn Hybrid Search kết hợp RRF (Reciprocal Rank Fusion) trên Qdrant."""
        logger.info(f"Đang thực thi Hybrid Search với RRF (limit={top_k})...")
        
        response = self.client.query_points(
            collection_name=settings.collection_name,
            prefetch=[
                # Kênh Dense Search
                models.Prefetch(
                    query=query_dense,
                    using=settings.dense_vector_name,
                    limit=settings.top_k_prefetch
                ),
                # Kênh Sparse Search (BM25)
                models.Prefetch(
                    query=query_sparse,
                    using=settings.sparse_vector_name,
                    limit=settings.top_k_prefetch
                ),
            ],
            # Áp dụng thuật toán Reciprocal Rank Fusion (RRF) ở cấp C++ Engine
            query=models.FusionQuery(
                fusion=models.Fusion.RRF
            ),
            limit=top_k
        )

        results: List[Dict[str, Any]] = []
        for point in response.points:
            results.append({
                "id": point.id,
                "score_rrf": point.score,
                "payload": point.payload
            })
        return results
