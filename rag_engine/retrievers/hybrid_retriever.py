#!/usr/bin/env python3
"""
Hybrid Search Retriever kết hợp Dense Vector (Qdrant) + Sparse Keyword (BM25)
sử dụng Thuật toán Hợp nhất Xếp hạng RRF (Reciprocal Rank Fusion).
"""

from typing import Dict, Any, List
from dense_retriever import DenseRetriever
from sparse_retriever import SparseRetriever


class HybridRetriever:
    def __init__(self, rrf_k: int = 60):
        self.dense_retriever = DenseRetriever()
        self.sparse_retriever = SparseRetriever()
        self.rrf_k = rrf_k

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm lai Hybrid Search kết hợp Dense + Sparse qua thuật toán RRF"""
        dense_results = self.dense_retriever.search(query, top_k=top_k * 2)
        sparse_results = self.sparse_retriever.search(query, top_k=top_k * 2)

        rrf_scores: Dict[str, float] = {}
        chunks_map: Dict[str, Dict[str, Any]] = {}

        # 1. Tính điểm RRF từ kết quả Dense Vector Search
        for rank, doc in enumerate(dense_results, 1):
            chunk_id = doc["chunk_id"]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))
            chunks_map[chunk_id] = doc

        # 2. Tính điểm RRF từ kết quả Sparse BM25 Keyword Search
        for rank, doc in enumerate(sparse_results, 1):
            chunk_id = doc["chunk_id"]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))
            if chunk_id not in chunks_map:
                chunks_map[chunk_id] = doc

        # 3. Sắp xếp lại theo điểm RRF giảm dần
        fused_results = []
        for chunk_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
            item = chunks_map[chunk_id].copy()
            item["rrf_score"] = float(score)
            fused_results.append(item)

        return fused_results[:top_k]


if __name__ == "__main__":
    retriever = HybridRetriever()
    res = retriever.search("Mô tả môn học Ngôn ngữ lập trình Python 124100", top_k=3)
    print(f"[*] Kết quả Hybrid Search (Dense + BM25 RRF):")
    for r in res:
        print(f"  - [RRF: {r['rrf_score']:.5f}] {r['chunk_id']}: {r['content'][:80]}...")
