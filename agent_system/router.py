#!/usr/bin/env python3
"""
AI Router & Intent Classifier (Bộ định tuyến ý định & Trích xuất môn học).
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
SUBJECTS_FILE = BASE_DIR / "structuring_data" / "json_collections" / "syllabus_subjects.json"


class AIRouter:
    def __init__(self):
        self.subject_catalog = {}
        self._load_subject_catalog()

    def _load_subject_catalog(self):
        """Tải danh mục 41 môn học để phục vụ Matching từ khóa"""
        if not SUBJECTS_FILE.exists():
            return
        with open(SUBJECTS_FILE, "r", encoding="utf-8") as f:
            subjects = json.load(f)

        for subj in subjects:
            code = subj.get("subject_code", "")
            name_vi = subj.get("subject_name_vi", "").lower()
            
            # Tạo các từ khóa nhận diện cho môn học này
            aliases = [code.lower(), name_vi]
            
            # Thêm từ khóa viết tắt hoặc rút gọn
            if "python" in name_vi:
                aliases.extend(["python", "lập trình python", "py"])
            elif "cơ sở dữ liệu" in name_vi:
                aliases.extend(["csdl", "cơ sở dữ liệu", "database", "db"])
            elif "trí tuệ nhân tạo" in name_vi:
                aliases.extend(["ai", "trí tuệ nhân tạo", "artificial intelligence"])
            elif "toán" in name_vi:
                aliases.extend(["toán cho máy", "phương pháp toán", "math"])

            self.subject_catalog[code] = {
                "code": code,
                "name_vi": subj.get("subject_name_vi", ""),
                "aliases": aliases
            }

    def route(self, user_prompt: str) -> Dict[str, Any]:
        """Phân tích câu hỏi, xác định Intent, trích xuất Subject Code và Confidence Score"""
        prompt_lower = user_prompt.lower()

        # 1. Phân loại Ý định (Intent Classification)
        intent = "syllabus_content"
        if any(w in prompt_lower for w in ["điểm", "thi", "rubric", "chuyên cần", "bài tập lớn", "đồ án", "%"]):
            intent = "grading_rubric"
        elif any(w in prompt_lower for w in ["plo", "po", "chuẩn đầu ra ngành", "lộ trình", "ra trường"]):
            intent = "curriculum_path"
        elif any(w in prompt_lower for w in ["chào", "hi", "hello", "bạn là ai"]):
            intent = "general_chat"

        # 2. Trích xuất Môn học & Tính điểm Tin cậy (Confidence Score)
        detected_code = None
        highest_score = 0.0
        matched_alias = None

        for code, info in self.subject_catalog.items():
            for alias in info["aliases"]:
                if alias in prompt_lower:
                    # Tính điểm tin cậy dựa trên độ dài từ khóa khớp
                    score = min(0.95, 0.6 + (len(alias) / 30.0))
                    if score > highest_score:
                        highest_score = score
                        detected_code = code
                        matched_alias = alias

        # 3. Ngưỡng An toàn (Confidence Threshold = 0.80)
        final_subject_code = None
        use_global_search = True

        if highest_score >= 0.80 and detected_code:
            final_subject_code = detected_code
            use_global_search = False
        else:
            final_subject_code = None
            use_global_search = True

        return {
            "query": user_prompt,
            "intent": intent,
            "detected_subject_code": detected_code,
            "matched_alias": matched_alias,
            "confidence_score": round(highest_score, 2),
            "final_subject_code": final_subject_code,
            "use_global_search": use_global_search
        }


if __name__ == "__main__":
    router = AIRouter()
    test_queries = [
        "Môn Lập trình Python học tuần mấy?",
        "Bài tập lớn môn AI chiếm bao nhiêu % điểm?",
        "PLO3 ngành Khoa học dữ liệu yêu cầu kỹ năng gì?",
        "Học phần nào ở trường dạy về thư viện Pandas?"
    ]
    
    print("=======================================================")
    print("🧪 THỬ NGHIỆM AI ROUTER (BỘ ĐỊNH TUYẾN Ý ĐỊNH)")
    print("=======================================================")
    for q in test_queries:
        res = router.route(q)
        print(f"\n❓ Câu hỏi: '{q}'")
        print(f"  ├─ Ý định (Intent):        {res['intent']}")
        print(f"  ├─ Môn nhận diện:           {res['detected_subject_code']} (Khớp từ: '{res['matched_alias']}')")
        print(f"  ├─ Độ tin cậy (Confidence): {res['confidence_score'] * 100}%")
        print(f"  └─ Quyết định RAG:          {'Duyệt 1 môn ' + str(res['final_subject_code']) if not res['use_global_search'] else 'Duyệt Toàn cục (Global Search)'}")
