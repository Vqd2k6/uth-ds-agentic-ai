#!/usr/bin/env python3
"""
AI Verifier & Fail-safe Engine (Bộ kiểm chứng & Chống sai lệch AI).
Kiểm tra chéo điểm số RAG, tự động phát hiện và hủy lọc môn nếu Router đoán sai.
"""

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

    def verify_and_retrieve(self, router_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Thực thi RAG dựa trên quyết định từ Router,
        sau đó Kiểm chứng điểm số (Verification) và Tự động Hủy lọc môn nếu phát hiện Router đoán sai.
        """
        query = router_result["query"]
        subject_code = router_result["final_subject_code"]
        use_global = router_result["use_global_search"]

        print(f"\n[*] VERIFIER: Đang kiểm chứng truy vấn cho câu hỏi: '{query}'")
        if subject_code:
            print(f"  ├─ Phạm vi lọc môn ban đầu: Môn {subject_code}")
        else:
            print(f"  ├─ Phạm vi ban đầu: Duyệt toàn cục (Global Search)")

        # 1. Chạy RAG thử nghiệm ban đầu
        rag_output = self.rag_engine.query(query, subject_code=subject_code if not use_global else None)
        hybrid_chunks = rag_output.get("hybrid_chunks", [])

        is_fallback_triggered = False
        fallback_reason = None

        # 2. KIỂM TRA CHỐT 2: Kiểm chứng điểm tương đồng RRF Score
        if not use_global and subject_code:
            top_score = hybrid_chunks[0]["rrf_score"] if hybrid_chunks else 0.0
            
            # Nếu lọc môn mà điểm RRF quá thấp (< threshold) -> Router đã đoán nhầm môn!
            if not hybrid_chunks or top_score < self.score_threshold:
                is_fallback_triggered = True
                fallback_reason = f"Điểm RRF quá thấp ({top_score:.5f} < {self.score_threshold}) do Router đoán nhầm môn '{subject_code}'"
                print(f"\n[⚠️ WARN VERIFIER]: Phát hiện Router đoán nhầm môn {subject_code}! {fallback_reason}")
                print("[🔄 AUTO FALLBACK]: Kích hoạt cơ chế HỦY LỌC MÔN -> Tự động chuyển sang DUYỆT TOÀN CỤC!")

                # Chạy lại RAG ở chế độ Duyệt toàn cục (No subject filter)
                rag_output = self.rag_engine.query(query, subject_code=None)
                hybrid_chunks = rag_output.get("hybrid_chunks", [])

        # 3. Tổng hợp kết quả Kiểm chứng
        verification_status = "VERIFIED_OK"
        if is_fallback_triggered:
            verification_status = "FALLBACK_TO_GLOBAL"
        elif not hybrid_chunks:
            verification_status = "NO_CONTEXT_FOUND"

        return {
            "query": query,
            "router_subject": subject_code,
            "verification_status": verification_status,
            "is_fallback_triggered": is_fallback_triggered,
            "fallback_reason": fallback_reason,
            "rag_output": rag_output,
            "final_chunks": hybrid_chunks,
            "formatted_context": rag_output.get("formatted_context", "")
        }

    def close(self):
        self.rag_engine.close()


if __name__ == "__main__":
    verifier = AIVerifier()
    
    # Giả lập tình huống Router ĐOÁN SAI MÔN (Hỏi về Python nhưng Router đoán nhầm môn CSDL 121000)
    fake_wrong_router = {
        "query": "Học phần Lập trình Python trang bị những kiến thức nào ở CLO1?",
        "final_subject_code": "121000", # Cố tình đoán sai môn Cơ sở dữ liệu!
        "use_global_search": False
    }

    res = verifier.verify_and_retrieve(fake_wrong_router)
    print("\n" + "=" * 65)
    print(f"📊 KẾT QUẢ KIỂM CHỨNG VERIFIER: {res['verification_status']}")
    print(f"  ├─ Router đoán nhầm môn: {res['router_subject']}")
    print(f"  ├─ Tự động sửa sai (Fallback): {res['is_fallback_triggered']}")
    print(f"  └─ Lý do: {res['fallback_reason']}")
    print("=" * 65)

    verifier.close()
