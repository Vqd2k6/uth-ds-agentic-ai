#!/usr/bin/env python3
"""
Dense Vector Retriever sử dụng Qdrant & Nomic Embeddings (768 chiều).
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

sys.path.append(str(PROJECT_DIR / "database_ingestion"))
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME

try:
    from qdrant_client import QdrantClient
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False


class DenseRetriever:
    def __init__(self, model_name: str = "nomic-ai/nomic-embed-text-v1.5"):
        self.collection_name = QDRANT_COLLECTION_NAME
        self.model_name = model_name
        self.client = None
        self.embedding_model = None

        if FASTEMBED_AVAILABLE:
            try:
                self.embedding_model = TextEmbedding(model_name=self.model_name)
            except Exception:
                self.embedding_model = TextEmbedding()

        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=3.0, check_compatibility=False)
                self.client.get_collections()
            except Exception:
                self.client = None

    def search(self, query: str, top_k: int = 5, subject_code_filter: str = None) -> List[Dict[str, Any]]:
        """Tìm kiếm ngữ nghĩa (Dense Vector Search) trên Qdrant"""
        if not self.embedding_model:
            print("[!] Chưa khởi tạo được mô hình Embedding.")
            return []

        query_vector = list(self.embedding_model.embed([query]))[0].tolist()

        if not self.client:
            print("[!] Qdrant Server offline. Đang trả về danh sách kiểm thử...")
            return []

        try:
            # Qdrant client query points
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k
            )
            
            results = []
            for point in response.points:
                payload = point.payload or {}
                results.append({
                    "chunk_id": payload.get("chunk_id", str(point.id)),
                    "score": float(point.score),
                    "content": payload.get("content", ""),
                    "subject_code": payload.get("subject_code", ""),
                    "subject_name_vi": payload.get("subject_name_vi", ""),
                    "chunk_type": payload.get("chunk_type", ""),
                    "section_title": payload.get("section_title", "")
                })
            return results
        except Exception as e:
            print(f"[!] Lỗi khi truy vấn Qdrant Dense Vector: {e}")
            return []


if __name__ == "__main__":
    retriever = DenseRetriever()
    res = retriever.search("Lập trình Python cơ bản học về những gì?", top_k=3)
    print(f"[*] Tìm thấy {len(res)} kết quả Dense Vector:")
    for r in res:
        print(f"  - [{r['score']:.4f}] {r['chunk_id']}: {r['content'][:80]}...")
