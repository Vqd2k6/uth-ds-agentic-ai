#!/usr/bin/env python3
"""
Local Open-Source LLM Client (Ollama Integration).
Tích hợp mô hình ngôn ngữ lớn chạy Local 100% (Qwen 2.5:3b / 7b)
tối ưu hóa cho Apple Silicon M1 (8GB Unified Memory).
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


class LocalLLMClient:
    def __init__(self, model_name: str = "qwen2.5:3b", host: str = "http://localhost:11434", timeout: int = 180):
        self.model_name = model_name
        self.host = host.rstrip("/")
        self.timeout = timeout
        self.system_prompt = (
            "Bạn là 'Trợ lý AI Cố vấn Học tập & Tri thức Ngành Khoa học Dữ liệu' tại Trường Đại học Giao thông Vận tải TP.HCM (UTH).\n"
            "Nhiệm vụ của bạn là tư vấn, giải thích và định hướng chi tiết cho sinh viên dựa trên Đề cương chi tiết học phần, Chuẩn đầu ra (CLO, PLO) và Khung chương trình đào tạo.\n\n"
            "### NGUYÊN TẮC BẮT BUỘC:\n"
            "1. Căn cứ trả lời: Dựa HOÀN TOÀN vào các đoạn trích xuất [NGỮ CẢNH TRI THỨC RAG] và [QUAN HỆ ĐỒ THỊ NEO4J] được cung cấp bên dưới.\n"
            "2. Chống bịa đặt (Hallucination): Nếu tài liệu không có thông tin được hỏi, hãy thông báo lịch sự rằng đề cương hiện tại chưa ghi nhận nội dung này thay vì tự suy đoán.\n"
            "3. Văn phong sư phạm: Điềm tĩnh, rõ ràng, khích lệ sinh viên, sử dụng định dạng Markdown chuyên nghiệp (gạch đầu dòng, in đậm các mã môn, chuẩn đầu ra, số tuần học, phần trăm điểm).\n"
            "4. Ngôn ngữ: Trả lời bằng Tiếng Việt chuẩn mực."
        )

    def is_available(self) -> bool:
        """Kiểm tra xem Ollama server có đang chạy và sẵn sàng không"""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def list_local_models(self) -> list:
        """Lấy danh sách các mô hình đã tải trong Ollama"""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m.get("name") for m in data.get("models", [])]
        except Exception:
            return []

    def generate(self, user_query: str, formatted_context: str, intent: str = "syllabus_content", chat_history: Optional[list] = None) -> str:
        """Sinh câu trả lời từ mô hình Open-Source LLM cục bộ có gắn kết lịch sử hội thoại"""
        if not self.is_available():
            return (
                "⚠️ [CẢNH BÁO LOCAL LLM]: Chưa kết nối được với Ollama Server tại `http://localhost:11434`.\n"
                "👉 Vui lòng mở Terminal và chạy lệnh: `ollama serve` để kích hoạt mô hình AI cục bộ.\n\n"
                "Dưới đây là dữ liệu thô trích xuất từ RAG Engine:\n" + formatted_context
            )

        # Xây dựng phần Lịch sử hội thoại (nếu có)
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_lines = []
            for turn in chat_history[-3:]:  # Lấy 3 lượt gần nhất
                role = "Sinh viên" if turn.get("role") == "user" else "Trợ lý AI"
                history_lines.append(f"{role}: {turn.get('content', '')}")
            history_text = "--- [LỊCH SỬ HỘI THOẠI TRƯỚC ĐÓ] ---\n" + "\n".join(history_lines) + "\n--- [HẾT PHẦN LỊCH SỬ] ---\n\n"

        # Xây dựng Prompt tổng hợp
        full_prompt = (
            f"{self.system_prompt}\n\n"
            f"{history_text}"
            f"--- [NGỮ CẢNH TRI THỨC ĐÍNH KÈM TỪ HỆ THỐNG RAG & KNOWLEDGE GRAPH] ---\n"
            f"{formatted_context if formatted_context.strip() else 'Không tìm thấy ngữ cảnh văn bản phù hợp.'}\n"
            f"--- [HẾT PHẦN NGỮ CẢNH] ---\n\n"
            f"Ý định truy vấn (Intent): {intent}\n"
            f"Câu hỏi hiện tại của sinh viên UTH: \"{user_query}\"\n\n"
            f"Hãy trả lời chi tiết, chính xác và bám sát ngữ cảnh môn học đang thảo luận:"
        )

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,   # Nhiệt độ thấp để bám sát dữ liệu thực tế, giảm hallucination
                "top_p": 0.9,
                "num_ctx": 2048,      # Context window tối ưu tốc độ và RAM cho chip M1 8GB
                "num_predict": 1024
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.host}/api/generate",
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json.get("response", "").strip()
        except urllib.error.URLError as e:
            return f"❌ Lỗi kết nối Ollama: {str(e)}"
        except Exception as e:
            return f"❌ Lỗi khi sinh phản hồi từ LLM: {str(e)}"


if __name__ == "__main__":
    client = LocalLLMClient(model_name="qwen2.5:3b")
    print(f"[*] Trạng thái kết nối Ollama: {'SẴN SÀNG' if client.is_available() else 'CHƯA BẬT'}")
    print(f"[*] Danh sách mô hình hiện có: {client.list_local_models()}")
