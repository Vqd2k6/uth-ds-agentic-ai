#!/usr/bin/env python3
"""
Sparse Keyword Retriever sử dụng BM25 (Exact Keyword Match).
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
CHUNKS_FILE_PATH = PROJECT_DIR / "structuring_data" / "json_collections" / "chunk_sources.json"


def tokenize_text(text: str) -> List[str]:
    """Tách từ đơn giản cho tiếng Việt và thuật ngữ chuyên ngành"""
    if not text:
        return []
    # Chuyển về chữ thường và tách từ theo khoảng trắng hoặc ký tự đặc biệt
    tokens = re.findall(r"\w+", text.lower())
    return tokens


class SparseRetriever:
    def __init__(self):
        self.chunks = []
        self.bm25 = None
        self._load_and_index_chunks()

    def _load_and_index_chunks(self):
        """Tải dữ liệu chunks và khởi tạo chỉ mục BM25"""
        if not CHUNKS_FILE_PATH.exists():
            return

        with open(CHUNKS_FILE_PATH, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        if BM25_AVAILABLE and self.chunks:
            corpus_tokens = [tokenize_text(item["content"]) for item in self.chunks]
            self.bm25 = BM25Okapi(corpus_tokens)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Tìm kiếm chính xác từ khóa bằng thuật toán BM25"""
        if not self.bm25 or not self.chunks:
            return []

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Sắp xếp kết quả theo điểm giảm dần
        scored_results = []
        for idx, score in enumerate(scores):
            if score > 0:
                item = self.chunks[idx]
                scored_results.append({
                    "chunk_id": item["chunk_id"],
                    "score": float(score),
                    "content": item["content"],
                    "subject_code": item["subject_code"],
                    "subject_name_vi": item["subject_name_vi"],
                    "chunk_type": item["chunk_type"],
                    "section_title": item["section_title"]
                })

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]


if __name__ == "__main__":
    retriever = SparseRetriever()
    res = retriever.search("Python 124100 CLO1", top_k=3)
    print(f"[*] Tìm thấy {len(res)} kết quả BM25 Keyword Search:")
    for r in res:
        print(f"  - [{r['score']:.4f}] {r['chunk_id']}: {r['content'][:80]}...")
