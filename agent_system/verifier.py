#!/usr/bin/env python3
"""
AI Verifier & Fact-Checking Engine (Bộ kiểm chứng 2 lớp: Ngữ cảnh RAG & Chống ảo giác LLM).
Lớp 1 (Pre-Retrieval Gatekeeper): Kiểm chứng điểm tin cậy RAG, chống định tuyến nhầm môn.
Lớp 2 (Post-Generation Fact-Checker): Kiểm chứng câu trả lời của LLM với tài liệu gốc, phát hiện và ngăn chặn ảo giác.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "rag_engine"))
from pipeline import RAGEngine


class AIVerifier:
    def __init__(self, score_threshold: float = 0.015):
        self.score_threshold = score_threshold
        self.rag_engine = RAGEngine()

    def retrieve_and_validate_context(self, router_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        LỚP 1 (Pre-Retrieval Gatekeeper):
        Thực thi RAG dựa trên quyết định từ Router, kiểm tra điểm số RRF.
        Tự động hủy lọc môn (fallback toàn cục) nếu phát hiện Router đoán nhầm môn làm mất ngữ cảnh.
        """
        query = router_result["query"]
        subject_code = router_result["final_subject_code"]
        use_global = router_result["use_global_search"]

        print(f"\n[BƯỚC 2: RAG & CONTEXT GATEKEEPER] Đang thu thập và thẩm định ngữ cảnh cho: '{query}'")
        if subject_code:
            print(f"  ├─ Phạm vi lọc môn: Môn {subject_code}")
        else:
            print(f"  ├─ Phạm vi: Duyệt toàn cục (Global Search)")

        # 1. Chạy RAG thử nghiệm ban đầu
        rag_output = self.rag_engine.query(query, subject_code=subject_code if not use_global else None)
        hybrid_chunks = rag_output.get("hybrid_chunks", [])

        is_fallback_triggered = False
        fallback_reason = None

        # 2. Kiểm chứng điểm tương đồng RRF Score
        if not use_global and subject_code:
            top_score = hybrid_chunks[0]["rrf_score"] if hybrid_chunks else 0.0
            
            # Nếu lọc môn mà điểm RRF quá thấp (< threshold) -> Router đã đoán nhầm môn!
            if not hybrid_chunks or top_score < self.score_threshold:
                is_fallback_triggered = True
                fallback_reason = f"Điểm RRF quá thấp ({top_score:.5f} < {self.score_threshold}) do Router đoán nhầm môn '{subject_code}'"
                print(f"  ├─ [⚠️ WARN]: Phát hiện Router đoán nhầm môn {subject_code}! {fallback_reason}")
                print("  ├─ [🔄 AUTO FALLBACK]: Kích hoạt cơ chế HỦY LỌC MÔN -> Tự động chuyển sang DUYỆT TOÀN CỤC!")

                # Chạy lại RAG ở chế độ Duyệt toàn cục (No subject filter)
                rag_output = self.rag_engine.query(query, subject_code=None)
                hybrid_chunks = rag_output.get("hybrid_chunks", [])

        gatekeeper_status = "CONTEXT_VERIFIED"
        if is_fallback_triggered:
            gatekeeper_status = "FALLBACK_GLOBAL_SEARCH"
        elif not hybrid_chunks:
            gatekeeper_status = "NO_CONTEXT_FOUND"

        return {
            "query": query,
            "gatekeeper_status": gatekeeper_status,
            "fallback_triggered": is_fallback_triggered,
            "fallback_reason": fallback_reason,
            "final_subject_code": subject_code if not is_fallback_triggered else None,
            "final_chunks": hybrid_chunks,
            "formatted_context": rag_output.get("formatted_context", ""),
            "graph_relationships": rag_output.get("graph_relationships", [])
        }

    def verify_llm_response(self, raw_answer: str, context_text: str, query: str) -> Dict[str, Any]:
        """
        LỚP 2 (Post-Generation Fact-Checker / Critic):
        Kiểm chứng câu trả lời do LLM sinh ra đối chiếu với tài liệu gốc (Ground Truth).
        - Phát hiện ảo giác (Hallucination Detection).
        - Kiểm tra tính trung thực của mã môn, tên giáo trình, chuẩn đầu ra được đề cập.
        """
        print(f"\n[BƯỚC 4: POST-GENERATION VERIFIER & FACT-CHECKER] Đang kiểm chứng tính chính xác của câu trả lời...")
        
        verification_flags = []
        is_grounded = True

        if not context_text or "KHÔNG CÓ THÔNG TIN" in raw_answer:
            return {
                "fact_check_status": "PASSED_UNMODIFIED",
                "is_grounded": True,
                "verified_answer": raw_answer,
                "notes": ["Câu trả lời chuẩn xác hoặc thông báo thiếu dữ liệu."]
            }

        # 1. Kiểm tra trích dẫn mã học phần trong câu trả lời
        mentioned_codes = re.findall(r"\b(\d{6})\b", raw_answer)
        for code in mentioned_codes:
            if code not in context_text:
                verification_flags.append(f"Cảnh báo: Mã môn {code} xuất hiện trong câu trả lời nhưng không có trong tài liệu trích xuất.")
                is_grounded = False

        # 2. Kiểm tra tính liên quan (Grounding Score)
        context_words = set(re.findall(r'\w+', context_text.lower()))
        answer_words = set(re.findall(r'\w+', raw_answer.lower()))
        common_words = context_words.intersection(answer_words)
        overlap_ratio = len(common_words) / max(len(answer_words), 1)

        if overlap_ratio < 0.25:
            verification_flags.append(f"Mức độ trùng khớp ngữ cảnh thấp ({overlap_ratio:.1%}). Có nguy cơ bị ảo giác ngoài tài liệu.")
            is_grounded = False

        status = "PASSED_VERIFIED" if is_grounded else "WARNING_UNGROUNDED"
        verified_answer = raw_answer
        
        if is_grounded:
            print(f"  ├─ [✓ FACT-CHECK OK]: Câu trả lời trung thực với tài liệu gốc (Độ phủ ngữ cảnh: {overlap_ratio:.1%}).")
        else:
            print(f"  ├─ [⚠️ FACT-CHECK WARN]: Phát hiện nghi vấn sai lệch: {'; '.join(verification_flags)}")

        return {
            "fact_check_status": status,
            "is_grounded": is_grounded,
            "overlap_ratio": round(overlap_ratio, 2),
            "verification_flags": verification_flags,
            "verified_answer": verified_answer
        }

    def close(self):
        self.rag_engine.close()
