#!/usr/bin/env python3
"""
Master RAG Pipeline: Kết hợp Hybrid Vector Search + Knowledge Graph Search.
Tổng hợp và định dạng Ngữ cảnh (Context) chuẩn bị cho Agentic AI / LLM.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).resolve().parent / "retrievers"))
from hybrid_retriever import HybridRetriever
from graph_retriever import GraphRetriever


class RAGEngine:
    def __init__(self):
        self.hybrid_retriever = HybridRetriever()
        self.graph_retriever = GraphRetriever()

    def query(self, user_prompt: str, subject_code: str = None, top_k: int = 4) -> Dict[str, Any]:
        """Thực thi pipeline tìm kiếm tri thức tổng hợp cho Agent"""
        print(f"\n=======================================================")
        print(f"🔍 RAG ENGINE: Đang xử lý câu hỏi: '{user_prompt}'")
        print(f"=======================================================")

        # 1. Truy xuất tri thức dạng Chunks (Hybrid Search Qdrant + BM25)
        hybrid_chunks = self.hybrid_retriever.search(user_prompt, top_k=top_k)
        
        # 2. Truy xuất tri thức dạng Đồ thị (Neo4j Graph) nếu có mã môn học
        graph_relations = []
        if subject_code:
            graph_relations = self.graph_retriever.query_subject_clos_and_plos(subject_code)

        # 3. Tổng hợp và Định dạng Ngữ cảnh (Context)
        context_parts = []
        
        context_parts.append("### 📚 TRI THỨC VĂN BẢN TRÍCH XUẤT (VECTOR & KEYWORD RAG):")
        if hybrid_chunks:
            for idx, item in enumerate(hybrid_chunks, 1):
                context_parts.append(
                    f"[{idx}] Môn: {item.get('subject_name_vi')} ({item.get('subject_code')})\n"
                    f"    Mục: {item.get('section_title')}\n"
                    f"    Nội dung: {item.get('content')}"
                )
        else:
            context_parts.append("Không tìm thấy đoạn tri thức phù hợp.")

        if graph_relations:
            context_parts.append("\n### 🌐 QUAN HỆ ĐỒ THỊ TRI THỨC (GRAPH RAG - NEO4J):")
            seen_rel = set()
            for r in graph_relations:
                clo = r.get("clo_code")
                plo = r.get("plo_id")
                level = r.get("contribution_level")
                if clo and plo and (clo, plo) not in seen_rel:
                    seen_rel.add((clo, plo))
                    context_parts.append(f"  - Chuẩn đầu ra {clo} đóng góp vào {plo} ở mức độ '{level}'")

        formatted_context = "\n\n".join(context_parts)

        return {
            "query": user_prompt,
            "hybrid_chunks": hybrid_chunks,
            "graph_relations": graph_relations,
            "formatted_context": formatted_context
        }

    def close(self):
        self.graph_retriever.close()


if __name__ == "__main__":
    engine = RAGEngine()
    res = engine.query("Lập trình Python học về biến và kiểu dữ liệu ở chuẩn đầu ra nào?", subject_code="124100")
    print("\n--- NGỮ CẢNH TỔNG HỢP CHO AGENT / LLM ---")
    print(res["formatted_context"])
    engine.close()
