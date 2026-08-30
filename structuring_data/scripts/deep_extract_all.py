#!/usr/bin/env python3
"""
Master Deep Extractor: Bóc tách toàn diện 100% dữ liệu từ thư mục 'output/'
- Đọc đồng thời cả file `.md` và `_content_list.json` của 41 môn học.
- Trích xuất: Thông tin chung, Mô tả, Mục tiêu (CO), Chuẩn đầu ra (CLO), Kế hoạch 15 tuần học, Giáo trình/Sách tham khảo, Bảng điểm đánh giá.
- Trích xuất: Khung CTĐT (PO1-PO6, PLO1-PLO7, PI2.1-PI7.2, Ma trận đóng góp 41 môn).
- Trích xuất: Danh mục Rubrics chi tiết (A1.1 -> A5.5 với thang điểm F, D, C, B, A).
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"
JSON_DIR = BASE_DIR / "json_collections"

SUBJECTS_JSON_PATH = JSON_DIR / "syllabus_subjects.json"
FRAMEWORKS_JSON_PATH = JSON_DIR / "outcome_frameworks.json"
RUBRICS_JSON_PATH = JSON_DIR / "rubric_catalog.json"


def clean_html_tags(text: str) -> str:
    """Làm sạch HTML tags và ký tự thừa"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\\-", "-", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_table_rows(html_table: str) -> List[List[str]]:
    """Chuyển chuỗi HTML table thành ma trận các ô văn bản"""
    rows = []
    tr_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", html_table, re.DOTALL | re.IGNORECASE)
    for tr in tr_matches:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.DOTALL | re.IGNORECASE)
        cleaned_cells = [clean_html_tags(c) for c in cells]
        if any(cleaned_cells):
            rows.append(cleaned_cells)
    return rows


def parse_single_subject(folder_path: Path) -> Optional[Dict[str, Any]]:
    """Phân tích một thư mục môn học trong output/"""
    content_list_files = list(folder_path.glob("**/*_content_list.json"))
    md_files = list(folder_path.glob("**/*.md"))

    if not content_list_files and not md_files:
        return None

    folder_name = folder_path.name
    code_match = re.search(r"(\d{6})", folder_name)
    subject_code = code_match.group(1) if code_match else "UNKNOWN"

    subject_data: Dict[str, Any] = {
        "subject_code": subject_code,
        "subject_name_vi": "",
        "subject_name_en": "",
        "credits": 3,
        "credit_breakdown": {"theory": 2, "practice": 1, "self_study": 3},
        "time_allocation": {"theory_exercises_projects": 30, "experiments_practice_discussion": 30, "total": 60, "self_study": 90},
        "grading_scale": 10,
        "prerequisite_subject_codes": [],
        "previous_subject_codes": [],
        "parallel_subject_codes": [],
        "course_type": "mandatory",
        "knowledge_block": "major",
        "description": "",
        "course_objectives": [],
        "clos": [],
        "student_duties": [],
        "assessment_methods": [],
        "teaching_plan": [],
        "main_textbooks": [],
        "reference_materials": []
    }

    md_text = ""
    if md_files:
        with open(md_files[0], "r", encoding="utf-8") as f:
            md_text = f.read()

    blocks = []
    if content_list_files:
        with open(content_list_files[0], "r", encoding="utf-8") as f:
            try:
                blocks = json.load(f)
            except Exception:
                blocks = []

    # Thu thập tất cả các HTML tables từ cả MD và JSON blocks
    all_html_tables = []
    for b in blocks:
        if b.get("type") == "table" and b.get("table_body"):
            all_html_tables.append(b.get("table_body"))

    md_tables = re.findall(r"(<table.*?>.*?</table>)", md_text, re.DOTALL | re.IGNORECASE)
    for tbl in md_tables:
        if tbl not in all_html_tables:
            all_html_tables.append(tbl)

    # 1. Bóc tách Thông tin chung từ Table 1
    for tbl in all_html_tables:
        if "Tên học phần" in tbl or "General course information" in tbl or "Số tín chỉ" in tbl:
            vi_match = re.search(r"Tiếng Việt:\s*([^<]+)", tbl, re.IGNORECASE)
            if vi_match:
                subject_data["subject_name_vi"] = clean_html_tags(vi_match.group(1)).replace("Tiếng Anh:", "").strip()
            en_match = re.search(r"Tiếng Anh:\s*([^<]+)", tbl, re.IGNORECASE)
            if en_match:
                subject_data["subject_name_en"] = clean_html_tags(en_match.group(1)).replace("Mã HP:", "").strip()
            tc_match = re.search(r"(\d+)\s*TC\s*\((\d+)[,\s]+(\d+)[,\s]+(\d+)\)", tbl)
            if tc_match:
                subject_data["credits"] = int(tc_match.group(1))
                subject_data["credit_breakdown"] = {
                    "theory": int(tc_match.group(2)),
                    "practice": int(tc_match.group(3)),
                    "self_study": int(tc_match.group(4))
                }
            prev_match = re.search(r"HP học trước\s*</td><td[^>]*>([^<]*)", tbl, re.IGNORECASE)
            if prev_match:
                prev_text = clean_html_tags(prev_match.group(1))
                subject_data["previous_subject_codes"] = re.findall(r"\d{6}", prev_text)
            break

    # Tên môn mặc định từ folder nếu chưa có
    if not subject_data["subject_name_vi"]:
        name_clean = re.sub(r"^\d+[\-_]*", "", folder_name)
        name_clean = re.sub(r"^\d{6}[\s\-_]*", "", name_clean)
        name_clean = re.sub(r"[\-_]DCCT.*$", "", name_clean, flags=re.IGNORECASE).strip()
        subject_data["subject_name_vi"] = name_clean

    # 2. Bóc tách Mô tả môn học
    desc_match = re.search(r"(?:2\.\s*Mô tả tóm tắt học phần|Course description)(.*?)(?:3\.\s*Mục tiêu|4\.\s*Chuẩn đầu ra)", md_text, re.DOTALL | re.IGNORECASE)
    if desc_match:
        subject_data["description"] = clean_html_tags(desc_match.group(1)).replace("##", "").strip()

    # 3. Bóc tách Mục tiêu môn học (COs)
    co_matches = re.findall(r"(?:✓\s*|\\\-\s*|\b)(CO\d+)[\s:\-]+([^\n✓#<]+)", md_text)
    for co_code, co_desc in co_matches:
        desc_clean = clean_html_tags(co_desc).strip()
        if len(desc_clean) > 5 and not any(co["co_code"] == co_code.upper() for co in subject_data["course_objectives"]):
            subject_data["course_objectives"].append({
                "co_code": co_code.upper(),
                "description": desc_clean
            })

    # 4. Bóc tách Chuẩn đầu ra môn học (CLOs)
    clo_matches = re.findall(r"(?:✓\s*|\\\-\s*|\b)(CLO\d+)[\s:\-]+([^\n✓#<]+)", md_text)
    if not clo_matches:
        clo_matches = re.findall(r"\b(CLO\d+)\s+([A-ZÀ-Ỹa-zà-ỹ][^\n<#]+)", md_text)

    for clo_code, clo_desc in clo_matches:
        desc_clean = clean_html_tags(clo_desc).strip()
        if len(desc_clean) > 10 and not desc_clean.startswith("<") and not any(c["clo_code"] == clo_code.upper() for c in subject_data["clos"]):
            subject_data["clos"].append({
                "clo_code": clo_code.upper(),
                "description": desc_clean
            })

    # 5. Bóc tách Nhiệm vụ của sinh viên
    duties_match = re.search(r"(?:5\.\s*Nhiệm vụ của sinh viên|Students duties)(.*?)(?:6\.\s*Phương pháp|7\.\s*Kế hoạch)", md_text, re.DOTALL | re.IGNORECASE)
    if duties_match:
        lines = [re.sub(r"^[\\\-\*\s]+", "", l).strip() for l in duties_match.group(1).split("\n") if l.strip()]
        subject_data["student_duties"] = [clean_html_tags(l) for l in lines if len(l) > 10 and not l.startswith("#")]

    # 6. Bóc tách Bảng Đánh giá & Rubrics
    for tbl in all_html_tables:
        if "Thành phần đánh giá" in tbl or "Đánh giá quá trình" in tbl or "Assessment methods" in tbl:
            rows = extract_table_rows(tbl)
            for r in rows:
                if len(r) >= 5 and "Thành phần" not in r[0] and "Tổng cộng" not in r[0]:
                    subject_data["assessment_methods"].append({
                        "component": r[0],
                        "method": r[1] if len(r) > 1 else "",
                        "clos": r[2] if len(r) > 2 else "",
                        "rubric_criteria": r[3] if len(r) > 3 else "",
                        "weight_percent": r[4] if len(r) > 4 else ""
                    })

    # 7. Bóc tách Kế hoạch 15 tuần học (Teaching Plan) qua TẤT CẢ các tables
    for tbl in all_html_tables:
        if any(keyword in tbl for keyword in ["Tuần /Chương", "Tuần / Chương", "Tuần/Chương", "Hoạt động dạy", "Dạngbàidánhgiá", "Bài đánh giá", "Kế hoạch giảng dạy"]):
            rows = extract_table_rows(tbl)
            for r in rows:
                if len(r) >= 2:
                    col0 = r[0].strip()
                    is_week_row = bool(re.search(r"^(?:Tuần|\d+[\-/]|\d+$|Chương|Buổi)", col0, re.IGNORECASE))
                    is_header = any(h in col0 for h in ["Tuần /Chương", "Tuần /", "Thành phần", "PLO/CLO", "Tên học phần", "Ký hiệu"])
                    
                    if (is_week_row or len(col0) < 25) and not is_header:
                        content = r[1] if len(r) > 1 else ""
                        clos = r[2] if len(r) > 2 else ""
                        activities = r[3] if len(r) > 3 else ""
                        assessment = r[4] if len(r) > 4 else ""
                        
                        if len(content) > 5 and not any(tp["week_or_chapter"] == col0 and tp["content"] == content for tp in subject_data["teaching_plan"]):
                            subject_data["teaching_plan"].append({
                                "week_or_chapter": col0,
                                "content": content,
                                "clos": clos,
                                "learning_activities": activities,
                                "assessment": assessment
                            })

    # 8. Bóc tách Giáo trình và Sách tham khảo từ Markdown và blocks
    main_match = re.search(r"(?:8\.1\.\s*Tài liệu chính|Main materials)(.*?)(?:8\.2\.\s*Tài liệu tham khảo|8\.2|9\.\s*Cơ sở vật chất|9\.)", md_text, re.DOTALL | re.IGNORECASE)
    if main_match:
        books = re.findall(r"\[\d+\]\s*([^\n]+)", main_match.group(1))
        subject_data["main_textbooks"] = [clean_html_tags(b) for b in books if len(b) > 5]

    ref_match = re.search(r"(?:8\.2\.\s*Tài liệu tham khảo|References materials)(.*?)(?:8\.3|9\.\s*Cơ sở vật chất|9\.|10\.)", md_text, re.DOTALL | re.IGNORECASE)
    if ref_match:
        books = re.findall(r"\[\d+\]\s*([^\n]+)", ref_match.group(1))
        subject_data["reference_materials"] = [clean_html_tags(b) for b in books if len(b) > 5]

    # Quét thêm từ blocks text nếu Markdown bị sót
    in_main_books = False
    in_ref_books = False
    for b in blocks:
        if b.get("type") == "text":
            txt = b.get("text", "").strip()
            if "8.1." in txt or "Tài liệu chính" in txt or "Main materials" in txt:
                in_main_books = True
                in_ref_books = False
                continue
            elif "8.2." in txt or "Tài liệu tham khảo" in txt or "References materials" in txt:
                in_main_books = False
                in_ref_books = True
                continue
            elif "8.3." in txt or "9." in txt or "Cơ sở vật chất" in txt:
                in_main_books = False
                in_ref_books = False
                continue

            if in_main_books and len(txt) > 10:
                cleaned_book = clean_html_tags(txt)
                if cleaned_book not in subject_data["main_textbooks"]:
                    subject_data["main_textbooks"].append(cleaned_book)
            elif in_ref_books and len(txt) > 10:
                cleaned_book = clean_html_tags(txt)
                if cleaned_book not in subject_data["reference_materials"]:
                    subject_data["reference_materials"].append(cleaned_book)

    return subject_data


def parse_plo_clo_rubric_file() -> tuple:
    """Trích xuất chi tiết PO, PLO, Ma trận đóng góp và Danh mục Rubric từ PLO-CLO-RUBRIC.md"""
    candidates = list(OUTPUT_DIR.glob("**/PLO-CLO-RUBRIC*.md"))
    if not candidates:
        return [], []

    with open(candidates[0], "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Trích xuất PO1 -> PO6
    pos = []
    po_matches = re.findall(r"(PO\d+)\.\s*([^\n]+)", content)
    for po_id, desc in po_matches:
        pos.append({
            "po_id": po_id,
            "description": clean_html_tags(desc).strip()
        })

    # 2. Trích xuất PLO1 -> PLO7 & Performance Indicators (PI)
    plos = []
    plo_table_match = re.search(r"## Chuẩn đầu ra của chương trình.*?<table>(.*?)</table>", content, re.DOTALL | re.IGNORECASE)
    if plo_table_match:
        rows = extract_table_rows(f"<table>{plo_table_match.group(1)}</table>")
        for r in rows:
            if len(r) >= 2 and r[0].startswith("PLO"):
                plos.append({
                    "plo_id": r[0].strip(),
                    "description": r[1].strip(),
                    "category": "knowledge_and_skills"
                })

    # 3. Trích xuất Ma trận đóng góp 6.3 vào PLO cho toàn bộ các môn học
    course_matrix = []
    matrix_table_match = re.search(r"6\.3\.\s*Ma trận mức độ đóng góp.*?<table>(.*?)</table>", content, re.DOTALL | re.IGNORECASE)
    if matrix_table_match:
        rows = extract_table_rows(f"<table>{matrix_table_match.group(1)}</table>")
        for r in rows:
            for idx, cell in enumerate(r):
                if re.match(r"^\d{6}$", cell):
                    subj_code = cell
                    subj_name = r[idx+1] if idx+1 < len(r) else ""
                    for c_idx in range(idx+2, len(r)):
                        val = r[c_idx].strip()
                        if any(level in val for level in ["I", "R", "M", "A"]):
                            plo_num = min(7, max(1, (c_idx - idx)))
                            course_matrix.append({
                                "subject_code": subj_code,
                                "subject_name": subj_name,
                                "plo_id": f"PLO{plo_num}",
                                "contribution_level": val
                            })
                    break

    framework = [{
        "framework_id": "khdl-uth-2024",
        "program_code": "7480201",
        "program_name": "Cử nhân Khoa học Dữ liệu - UTH",
        "pos": pos,
        "plos": plos,
        "course_contribution_plo_matrix": course_matrix
    }]

    # 4. Trích xuất Phụ lục Rubrics chi tiết (Rubric A1.1 -> A5.5)
    rubrics = []
    rubric_sections = re.findall(r"Rubric\s*(A\d+\.\d+):\s*([^\n<]+).*?<table>(.*?)</table>", content, re.DOTALL | re.IGNORECASE)
    for rub_code, rub_name, rub_table in rubric_sections:
        rub_id = f"RUBRIC_{rub_code.strip()}"
        criteria = []
        rows = extract_table_rows(f"<table>{rub_table}</table>")
        for r in rows:
            if len(r) >= 6 and not any(h in r[0] for h in ["Tiêu chí", "MỨC"]):
                crit_name = r[0]
                weight = r[-1] if len(r) > 1 else ""
                criteria.append({
                    "criterion_name": crit_name,
                    "levels": {
                        "F": r[1] if len(r) > 1 else "",
                        "D": r[2] if len(r) > 2 else "",
                        "C": r[3] if len(r) > 3 else "",
                        "B": r[4] if len(r) > 4 else "",
                        "A": r[5] if len(r) > 5 else ""
                    },
                    "weight": weight
                })

        rubrics.append({
            "rubric_id": rub_id,
            "assessment_code": rub_code.strip(),
            "assessment_name": rub_name.strip(),
            "criteria": criteria
        })

    return framework, rubrics


def run_full_extraction():
    print("=" * 70)
    print("🚀 BẮT ĐẦU MASTER DEEP EXTRACTION TỪ THƯ MỤC 'output/'")
    print("=" * 70)
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    all_subjects = []
    for item in sorted(OUTPUT_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith(".") and item.name not in ["Rubric", "PLO-CLO-RUBRIC"]:
            subj_data = parse_single_subject(item)
            if subj_data and subj_data["subject_code"] != "UNKNOWN":
                all_subjects.append(subj_data)
                print(f"  [✓] Môn {subj_data['subject_code']}: {subj_data['subject_name_vi']} | Tuần: {len(subj_data['teaching_plan'])} | CLOs: {len(subj_data['clos'])} | Sách: {len(subj_data['main_textbooks'])+len(subj_data['reference_materials'])}")

    with open(SUBJECTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_subjects, f, ensure_ascii=False, indent=2)
    print(f"\n[✓] Đã xuất {len(all_subjects)} môn học chi tiết vào: {SUBJECTS_JSON_PATH.name}")

    framework, rubrics = parse_plo_clo_rubric_file()
    if framework:
        with open(FRAMEWORKS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(framework, f, ensure_ascii=False, indent=2)
        print(f"[✓] Đã xuất Khung CTĐT ({len(framework[0]['pos'])} POs, {len(framework[0]['plos'])} PLOs, {len(framework[0]['course_contribution_plo_matrix'])} Ma trận đóng góp) vào: {FRAMEWORKS_JSON_PATH.name}")

    if rubrics:
        with open(RUBRICS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(rubrics, f, ensure_ascii=False, indent=2)
        print(f"[✓] Đã xuất {len(rubrics)} Rubrics tiêu chí điểm số chi tiết vào: {RUBRICS_JSON_PATH.name}")

    print("\n" + "=" * 70)
    print("🎉 HOÀN TẤT MASTER DEEP EXTRACTION DỮ LIỆU!")
    print("=" * 70)


if __name__ == "__main__":
    run_full_extraction()
