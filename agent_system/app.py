#!/usr/bin/env python3
"""
Master Agent System Pipeline (Ứng dụng Tác tử Thông minh End-to-End).
Quy trình Chuẩn Agentic AI 4 Bước với Bộ nhớ Ngữ cảnh Hội thoại (Multi-turn Context Memory):
  1. AI Router: Nhận diện Ý định, Ánh xạ môn học & Giải quyết đại từ thay thế (Anaphora Resolution).
  2. Context Gatekeeper & Hybrid RAG: Thẩm định & Thu thập tri thức từ Vector Qdrant + Đồ thị Neo4j.
  3. LLM Generator: Sinh câu trả lời dựa trên ngữ cảnh và lịch sử hội thoại (Local Qwen2.5 trên Apple M1).
  4. Post-Generation Verifier: Kiểm chứng câu trả lời, đối chiếu tài liệu gốc chống ảo giác.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from router import AIRouter
from verifier import AIVerifier
from llm_client import LocalLLMClient


class AgentSystemApp:
    def __init__(self, model_name: str = "qwen2.5:3b"):
        self.model_name = model_name
        self.router = AIRouter()
        self.verifier = AIVerifier()
        self.llm = LocalLLMClient(model_name=model_name)
        
        # Bộ nhớ phiên hội thoại (Conversational Memory)
        self.chat_history: List[Dict[str, str]] = []
        self.active_subject_code: Optional[str] = None

    def reset_session(self):
        """Khởi tạo lại phiên trò chuyện mới"""
        self.chat_history = []
        self.active_subject_code = None
        print("[ℹ️ SESSION]: Đã làm mới bộ nhớ hội thoại.")

    def chat(self, user_prompt: str) -> Dict[str, Any]:
        """Xử lý câu hỏi của sinh viên theo toàn bộ luồng Agentic AI 4 Bước chuẩn chỉnh"""
        print(f"\n" + "=" * 65)
        print(f"🤖 AGENT SYSTEM: Tiếp nhận câu hỏi: '{user_prompt}'")
        print(f"=" * 65)

        # ---------------------------------------------------------------------
        # BƯỚC 1: AI ROUTER (Phân loại ý định & Trích xuất môn học có nhớ ngữ cảnh)
        # ---------------------------------------------------------------------
        router_res = self.router.route(
            user_prompt=user_prompt,
            active_subject_code=self.active_subject_code,
            chat_history=self.chat_history
        )
        
        # Cập nhật môn học đang thảo luận trong phiên
        if router_res.get("final_subject_code"):
            self.active_subject_code = router_res["final_subject_code"]

        inherited_tag = " [Kế thừa ngữ cảnh]" if router_res.get("is_context_inherited") else ""
        print(f"[BƯỚC 1: ROUTER] Intent: '{router_res['intent']}' | Môn: {router_res['final_subject_code']} ({router_res.get('matched_alias') or 'Không'}){inherited_tag} | Tin cậy: {router_res['confidence_score']*100:.0f}%")
        if router_res.get("is_context_inherited"):
            print(f"  └─ Tái cấu trúc câu truy vấn RAG: '{router_res.get('rewritten_query')}'")

        # Xử lý nhanh câu chào hỏi thông thường
        if router_res["intent"] == "general_chat":
            quick_reply = (
                "Xin chào! Tôi là Trợ lý AI Cố vấn Học tập & Tri thức Ngành Khoa học Dữ liệu (UTH).\n"
                "Tôi có thể hỗ trợ bạn tra cứu chi tiết về:\n"
                "  • Đề cương chi tiết 41 môn học (kế hoạch tuần, giáo trình, chuẩn đầu ra CLO).\n"
                "  • Chuẩn đầu ra ngành (PLO), mục tiêu đào tạo (PO) và ma trận đóng góp.\n"
                "  • Thang điểm, tiêu chí đánh giá và Rubric chấm bài tập lớn/thi cử.\n\n"
                "Bạn cần tôi hỗ trợ tìm kiếm thông tin về học phần nào?"
            )
            # Lưu lịch sử
            self.chat_history.append({"role": "user", "content": user_prompt})
            self.chat_history.append({"role": "assistant", "content": quick_reply})
            return {
                "query": user_prompt,
                "router": router_res,
                "gatekeeper": {"gatekeeper_status": "SKIPPED_GENERAL_CHAT"},
                "llm_output": quick_reply,
                "verifier": {"fact_check_status": "PASSED_GENERAL_CHAT"},
                "final_answer": quick_reply
            }

        # ---------------------------------------------------------------------
        # BƯỚC 2: CONTEXT GATEKEEPER & HYBRID RAG (Thu thập & Thẩm định ngữ cảnh)
        # Sử dụng rewritten_query nếu câu hỏi có đại từ thay thế
        # ---------------------------------------------------------------------
        gatekeeper_input = dict(router_res)
        if router_res.get("is_context_inherited") and router_res.get("rewritten_query"):
            gatekeeper_input["query"] = router_res["rewritten_query"]

        gatekeeper_res = self.verifier.retrieve_and_validate_context(gatekeeper_input)
        formatted_context = gatekeeper_res.get("formatted_context", "")

        # ---------------------------------------------------------------------
        # BƯỚC 3: LLM GENERATOR (Sinh câu trả lời từ ngữ cảnh RAG + Chat History)
        # ---------------------------------------------------------------------
        print(f"\n[BƯỚC 3: LLM GENERATOR] Đang sinh câu trả lời với mô hình '{self.model_name}'...")
        raw_answer = self.llm.generate(
            user_query=user_prompt,
            formatted_context=formatted_context,
            intent=router_res["intent"],
            chat_history=self.chat_history
        )

        # ---------------------------------------------------------------------
        # BƯỚC 4: POST-GENERATION VERIFIER (Kiểm chứng sự thật & Chống ảo giác)
        # ---------------------------------------------------------------------
        fact_check_res = self.verifier.verify_llm_response(
            raw_answer=raw_answer,
            context_text=formatted_context,
            query=user_prompt
        )

        final_answer = fact_check_res["verified_answer"]

        # Cập nhật lịch sử hội thoại cho các lượt tiếp theo
        self.chat_history.append({"role": "user", "content": user_prompt})
        self.chat_history.append({"role": "assistant", "content": final_answer})

        return {
            "query": user_prompt,
            "router": router_res,
            "gatekeeper": gatekeeper_res,
            "raw_answer": raw_answer,
            "verifier": fact_check_res,
            "final_answer": final_answer
        }

    def close(self):
        self.verifier.close()


if __name__ == "__main__":
    app = AgentSystemApp()
    print("--- KIỂM THỬ HỘI THOẠI ĐA LƯỢT (MULTI-TURN CONVERSATION) ---")
    
    # Lượt 1: Hỏi về môn Triết học
    res1 = app.chat("Học phần Triết học Mác - Lênin đóng góp vào PLO nào?")
    print(f"\n[PHẢN HỒI LƯỢT 1]:\n{res1['final_answer'][:300]}...\n")
    
    # Lượt 2: Hỏi tiếp đại từ 'cách thức tính điểm của nó là gì'
    res2 = app.chat("cách thức tính điểm của nó là gì")
    print(f"\n[PHẢN HỒI LƯỢT 2]:\n{res2['final_answer'][:300]}...\n")
