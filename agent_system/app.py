#!/usr/bin/env python3
"""
Master Agent System Pipeline (Ứng dụng Tác tử Thông minh End-to-End).
Kết nối Router -> Verifier -> Hybrid RAG -> Neo4j Graph -> LLM Response Generator.
"""

import sys
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from router import AIRouter
from verifier import AIVerifier


class AgentSystemApp:
    def __init__(self):
        self.router = AIRouter()
        self.verifier = AIVerifier()

    def chat(self, user_prompt: str) -> Dict[str, Any]:
        """Xử lý câu hỏi của sinh viên theo toàn bộ luồng Agentic Workflow"""
        print(f"\n=======================================================")
        print(f"🤖 AGENT SYSTEM: Tiếp nhận câu hỏi: '{user_prompt}'")
        print(f"=======================================================")

        # 1. AI Router: Phân loại ý định & Trích xuất mã môn
        router_res = self.router.route(user_prompt)
        print(f"[1. ROUTER] Intent: '{router_res['intent']}' | Môn: {router_res['final_subject_code']} | Tin cậy: {router_res['confidence_score']*100:.0f}%")

        # 2. AI Verifier & RAG Retrieval: Kiểm chứng & Truy xuất tri thức
        verifier_res = self.verifier.verify_and_retrieve(router_res)
        print(f"[2. VERIFIER] Trạng thái: {verifier_res['verification_status']} | Chunks: {len(verifier_res['final_chunks'])}")

        # 3. Layer Agent: Tổng hợp câu trả lời hoàn chỉnh cho Sinh viên
        answer = self._generate_agent_response(user_prompt, router_res, verifier_res)

        return {
            "query": user_prompt,
            "router": router_res,
            "verifier": verifier_res,
            "final_answer": answer
        }

    def _generate_agent_response(self, prompt: str, router_res: Dict[str, Any], verifier_res: Dict[str, Any]) -> str:
        """Tạo phản hồi tự nhiên tổng hợp cho Sinh viên"""
        intent = router_res["intent"]
        chunks = verifier_res.get("final_chunks", [])
        graph_rels = verifier_res.get("rag_output", {}).get("graph_relations", [])

        if intent == "general_chat":
            return "Xin chào! Tôi là Trợ lý AI Cố vấn Học tập cho Sinh viên Khoa học Dữ liệu (UTH). Bạn cần tôi hỗ trợ tra cứu về học phần, chuẩn đầu ra hay tiêu chí điểm số nào?"

        if not chunks and not graph_rels:
            return "Rất tiếc, tôi chưa tìm thấy thông tin phù hợp trong bộ đề cương học phần. Bạn có thể thử đặt câu hỏi khác hoặc cung cấp thêm tên môn học nhé!"

        # Dựng câu trả lời tự nhiên dựa trên tri thức đã bóc tách
        lines = []
        lines.append(f"Dưới đây là thông tin tra cứu cho câu hỏi của bạn về '{prompt}':\n")

        # Thêm thông tin tri thức văn bản
        for idx, chunk in enumerate(chunks[:3], 1):
            subj_name = chunk.get("subject_name_vi", "")
            code = chunk.get("subject_code", "")
            sec = chunk.get("section_title", "")
            content = chunk.get("content", "")
            lines.append(f"📌 **[{idx}] Học phần {subj_name} ({code}) - {sec}**:")
            lines.append(f"   {content}\n")

        # Thêm thông tin chuẩn đầu ra từ Neo4j Graph
        if graph_rels:
            lines.append("🎓 **Thông tin Ma trận Chuẩn đầu ra (Knowledge Graph Neo4j)**:")
            seen = set()
            for r in graph_rels[:4]:
                clo = r.get("clo_code")
                plo = r.get("plo_id")
                level = r.get("contribution_level")
                if clo and plo and (clo, plo) not in seen:
                    seen.add((clo, plo))
                    lines.append(f"   - Chuẩn đầu ra môn {clo} đóng góp vào Chuẩn đầu ra ngành {plo} ở mức độ '{level}'")

        return "\n".join(lines)

    def close(self):
        self.verifier.close()


if __name__ == "__main__":
    app = AgentSystemApp()
    res = app.chat("Lập trình Python cơ bản gồm những kiến thức gì?")
    print("\n" + "=" * 65)
    print("💬 PHẢN HỒI HOÀN CHỈNH TỪ AGENT SYSTEM:")
    print("=" * 65)
    print(res["final_answer"])
    print("=" * 65)
    app.close()
