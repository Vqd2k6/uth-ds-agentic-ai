#!/usr/bin/env python3
"""
AI Router & Intent Classifier (Bộ định tuyến ý định, Trích xuất môn học & Nhớ ngữ cảnh hội thoại).
Hỗ trợ:
- Nhận diện toàn diện 41 môn học qua Mã môn, Tên tiếng Việt, Tên tiếng Anh, Tên viết tắt.
- Giải quyết đại từ thay thế (Anaphora Resolution): 'nó', 'môn này', 'học phần đó', 'môn vừa nói', 'ở tuần mấy', 'tính điểm thế nào'.
- Tái cấu trúc câu hỏi (Contextual Query Rewriting) phục vụ truy xuất RAG chính xác.
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
        """Tải danh mục 41 môn học và xây dựng bộ từ điển Alias chuyên sâu cho từng môn"""
        if not SUBJECTS_FILE.exists():
            return
        with open(SUBJECTS_FILE, "r", encoding="utf-8") as f:
            subjects = json.load(f)

        custom_aliases = {
            # Thị giác máy tính & Xử lý ảnh
            "121036": ["thị giác máy tính", "thi giac may tinh", "xử lý ảnh", "xu ly anh", "computer vision", "image processing", "xử lý ảnh và thị giác máy tính", "cv", "ipcv"],
            "127117": ["chuyên đề thị giác máy tính", "chuyen de thi giac may tinh", "chuyên đề cv", "special topics of computer vision"],
            
            # Trí tuệ nhân tạo, Học máy & Học sâu
            "121033": ["trí tuệ nhân tạo", "tri tue nhan tao", "artificial intelligence", "ai", "ttnt"],
            "127104": ["máy học", "may hoc", "học máy", "hoc may", "machine learning", "ml"],
            "127105": ["học sâu", "hoc sau", "deep learning", "dl", "mạng neural", "ann", "cnn"],
            "127108": ["học tăng cường", "hoc tang cuong", "reinforcement learning", "rl"],
            "127102": ["toán cho máy học", "toan cho may hoc", "phương pháp toán cho máy học", "math for ml", "toán học máy", "các phương pháp toán"],
            
            # Xử lý ngôn ngữ tự nhiên & Âm thanh
            "127111": ["xử lý ngôn ngữ tự nhiên", "ngôn ngữ tự nhiên", "nlp", "xử lý giọng nói", "âm thanh", "speech and nlp", "xử lý giọng nói, âm thanh"],
            "127118": ["chuyên đề xử lý ngôn ngữ tự nhiên", "chuyên đề nlp", "special topics of nlp"],
            
            # Chuỗi thời gian & Dự báo
            "127109": ["chuỗi thời gian", "chuoi thoi gian", "dự báo", "du bao", "time series", "time series forecasting"],
            "127119": ["chuyên đề chuỗi thời gian", "chuyên đề dự báo", "chuyen de chuoi thoi gian"],
            
            # Lập trình & Kỹ thuật lập trình
            "124100": ["python", "lập trình python", "ngôn ngữ python", "py", "python programming"],
            "124101": ["kỹ thuật lập trình", "ky thuat lap trinh", "ktlt", "programming techniques"],
            "122003": ["hướng đối tượng", "lập trình hướng đối tượng", "huong doi tuong", "oop", "object oriented programming", "java", "c++"],
            "121031": ["lập trình web", "lap trinh web", "web programming", "web", "html", "css"],
            "127123": ["javascript", "typescript", "js", "ts", "lập trình javascript"],
            
            # Cơ sở dữ liệu & Hệ thống
            "121000": ["cơ sở dữ liệu", "co so du lieu", "csdl", "database system", "database", "sql"],
            "121002": ["thiết kế cơ sở dữ liệu", "thiết kế csdl", "thiet ke csdl", "database design"],
            "121003": ["hệ quản trị cơ sở dữ liệu", "hệ quản trị csdl", "he quan tri csdl", "dbms", "database management"],
            "121008": ["phân tích thiết kế hệ thống", "phan tich thiet ke he thong", "pttkht", "systems analysis", "sad"],
            
            # Khai thác dữ liệu, Trực quan hóa & Big Data
            "122041": ["khai thác dữ liệu", "khai phá dữ liệu", "khai pha du lieu", "data mining", "dm"],
            "127106": ["trực quan hóa dữ liệu", "truc quan hoa du lieu", "trực quan hóa", "data visualization", "dataviz"],
            "127110": ["big data", "dữ liệu lớn", "du lieu lon", "big data và ứng dụng", "hadoop", "spark"],
            "127100": ["định tính và định lượng", "dinh tinh va dinh luong", "phân tích định tính", "phân tích định lượng", "qualitative and quantitative"],
            
            # Blockchain
            "127101": ["blockchain", "hợp đồng thông minh", "smart contract", "lập trình blockchain"],
            "127112": ["cấu trúc blockchain", "mạng blockchain", "hệ thống blockchain", "blockchain network"],
            
            # Nền tảng KHDL, Cấu trúc dữ liệu & Thuật toán
            "122102": ["nhập môn ngành khoa học dữ liệu", "nhập môn khoa học dữ liệu", "nhap mon khdl", "nhập môn ngành", "intro data science"],
            "124002": ["cấu trúc dữ liệu và giải thuật", "cấu trúc dữ liệu", "cau truc du lieu", "ctdl", "data structures", "dsa"],
            "124003": ["phân tích thiết kế giải thuật", "thiết kế giải thuật", "algorithms analysis"],
            "122044": ["cấu trúc rời rạc", "cau truc roi rac", "toán rời rạc", "discrete structures"],
            "122005": ["công nghệ phần mềm", "cong nghe phan mem", "software engineering", "cnpm", "se"],
            "123033": ["an toàn thông tin", "an toan thong tin", "bảo mật", "information security", "attt"],
            "123039": ["điện toán đám mây", "dien toan dam may", "cloud computing", "cloud"],
            "121137": ["quản trị doanh nghiệp cntt", "quản trị doanh nghiệp", "it enterprise management"],
            
            # Lý luận chính trị & Đại cương
            "005105": ["triết học", "triet hoc", "triết học mác - lênin", "triết học mác", "mác lênin", "005105"],
            "005106": ["kinh tế chính trị", "kinh te chinh tri", "005106"],
            "005107": ["chủ nghĩa xã hội", "chủ nghĩa xã hội khoa học", "cnxh", "005107"],
            "005102": ["tư tưởng hồ chí minh", "tư tưởng hcm", "005102"],
            "005108": ["lịch sử đảng", "lịch sử đảng csvn", "005108"],
            "005004": ["pháp luật đại cương", "phap luat dai cuong", "005004"],
            "001212": ["xác suất thống kê", "xác suất", "thống kê", "xstk", "001212"],
            "080101": ["phương pháp nghiên cứu", "nghiên cứu khoa học", "080101"],
            "080102": ["quản trị học", "quan tri hoc", "080102"],
            "080103": ["tư duy thiết kế", "đổi mới sáng tạo", "design thinking", "080103"],
            "125000": ["kiến trúc máy tính", "kien truc may tinh", "125000"],

            # Thực tập, Đồ án & Tốt nghiệp
            "127107": ["đồ án thực tế", "do an thuc te", "capstone project", "đồ án ksdl", "đồ án"],
            "126003": ["học kỳ doanh nghiệp", "hoc ky doanh nghiep", "hkdn"],
            "126000": ["thực tập tốt nghiệp", "thuc tap tot nghiep", "tttn", "internship"],
            "126201": ["khóa luận tốt nghiệp", "khoa luan tot nghiep", "kltn", "thesis"]
        }

        for subj in subjects:
            code = subj.get("subject_code", "")
            name_vi = subj.get("subject_name_vi", "").strip().lower()
            name_en = subj.get("subject_name_en", "").strip().lower()
            
            aliases = [code.lower()]
            if name_vi:
                aliases.append(name_vi)
            if name_en:
                aliases.append(name_en)
            
            if code in custom_aliases:
                aliases.extend(custom_aliases[code])

            self.subject_catalog[code] = {
                "code": code,
                "name_vi": subj.get("subject_name_vi", "") or name_en.upper(),
                "aliases": list(set([a for a in aliases if a]))
            }

        # Bổ sung các môn đại cương vào catalog nếu chưa có
        for extra_code, extra_aliases in custom_aliases.items():
            if extra_code not in self.subject_catalog:
                self.subject_catalog[extra_code] = {
                    "code": extra_code,
                    "name_vi": extra_aliases[0].title(),
                    "aliases": list(set([extra_code.lower()] + extra_aliases))
                }

    def route(self, user_prompt: str, active_subject_code: Optional[str] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Phân tích câu hỏi, giải quyết đại từ ngữ cảnh (Anaphora Resolution) và trích xuất Subject Code.
        """
        prompt_lower = user_prompt.lower()

        # 1. Phân loại Ý định (Intent Classification)
        intent = "syllabus_content"
        if any(w in prompt_lower for w in ["điểm", "tính điểm", "thi", "rubric", "chuyên cần", "bài tập lớn", "đồ án", "%", "trọng số", "thang điểm"]):
            intent = "grading_rubric"
        elif any(w in prompt_lower for w in ["plo", "po", "chuẩn đầu ra ngành", "lộ trình", "ra trường", "mục tiêu đào tạo", "học kỳ"]):
            intent = "curriculum_path"
        elif any(w in prompt_lower for w in ["chào", "hi", "hello", "bạn là ai", "giúp gì"]):
            intent = "general_chat"

        # 2. Trích xuất Môn học từ câu hỏi hiện tại
        detected_code = None
        highest_score = 0.0
        matched_alias = None

        all_matches = []
        for code, info in self.subject_catalog.items():
            for alias in info["aliases"]:
                matched = False
                if len(alias) <= 3:
                    if re.search(r'\b' + re.escape(alias) + r'\b', prompt_lower):
                        matched = True
                else:
                    if alias in prompt_lower:
                        matched = True

                if matched:
                    if alias == "ai" and intent == "general_chat":
                        continue

                    if alias == code.lower():
                        score = 1.0
                    else:
                        score = min(0.95, 0.70 + (len(alias) / 40.0))
                    all_matches.append((score, len(alias), code, alias))

        if all_matches:
            all_matches.sort(key=lambda x: (x[0], x[1]), reverse=True)
            highest_score, _, detected_code, matched_alias = all_matches[0]

        # 3. KÍCH HOẠT ANAPHORA RESOLUTION (Bộ nhớ Ngữ cảnh & Đại từ thay thế)
        is_context_inherited = False
        rewritten_query = user_prompt

        # Danh sách các từ chỉ định ngữ cảnh câu hỏi nối tiếp
        pronoun_signals = ["nó", "môn này", "học phần này", "môn đó", "môn trên", "học phần đó", "môn vừa nói", "ở tuần", "giáo trình gì", "tính điểm", "tiêu chí", "mấy tín chỉ"]
        has_pronoun = any(p in prompt_lower for p in pronoun_signals)

        if not detected_code and active_subject_code and active_subject_code in self.subject_catalog:
            # Nếu câu hỏi hiện tại không nêu tên môn mới nhưng có đại từ hoặc hỏi tiếp tục
            if has_pronoun or intent in ["syllabus_content", "grading_rubric"]:
                detected_code = active_subject_code
                highest_score = 0.90
                matched_alias = f"ngữ cảnh môn trước ({active_subject_code})"
                is_context_inherited = True
                
                # Tái cấu trúc câu hỏi cho RAG để tìm kiếm chính xác tuyệt đối
                active_subj_name = self.subject_catalog[active_subject_code]["name_vi"]
                rewritten_query = f"{user_prompt} của môn học {active_subj_name} (mã {active_subject_code})"

        # 4. Ngưỡng An toàn
        final_subject_code = None
        use_global_search = True

        if highest_score >= 0.70 and detected_code:
            final_subject_code = detected_code
            use_global_search = False
        else:
            final_subject_code = None
            use_global_search = True

        return {
            "query": user_prompt,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "detected_subject_code": detected_code,
            "confidence_score": round(highest_score, 2),
            "matched_alias": matched_alias,
            "final_subject_code": final_subject_code,
            "use_global_search": use_global_search,
            "is_context_inherited": is_context_inherited
        }


if __name__ == "__main__":
    router = AIRouter()
    print("--- KIỂM THỬ ANAPHORA RESOLUTION (BỘ NHỚ NGỮ CẢNH) ---")
    # Giả lập hội thoại 2 lượt:
    # Lượt 1: Hỏi về Triết học
    res1 = router.route("Môn Triết học Mác - Lênin học những gì?")
    print(f"Lượt 1: '{res1['query']}' -> Môn: {res1['final_subject_code']} ({res1['matched_alias']})")
    
    # Lượt 2: Hỏi tiếp 'cách thức tính điểm của nó là gì' với active_subject_code='005105'
    res2 = router.route("cách thức tính điểm của nó là gì", active_subject_code=res1['final_subject_code'])
    print(f"Lượt 2: '{res2['query']}' -> Môn kế thừa: {res2['final_subject_code']} | Rewritten Query: '{res2['rewritten_query']}'")
