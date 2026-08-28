#!/usr/bin/env python3
"""
Script trích xuất Collection 'syllabus_subjects' từ Đề cương chi tiết học phần (Markdown).
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List

# Đường dẫn mặc định
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
PARSED_OUTPUT_DIR = PROJECT_DIR / "preprocessing_data" / "parsed_output"
OUTPUT_JSON_PATH = BASE_DIR / "json_collections" / "syllabus_subjects.json"


def parse_subject_markdown(md_content: str, subject_folder_name: str) -> Dict[Any, Any]:
    """
    Phân tích file Markdown đề cương môn học và trích xuất các trường thông tin theo Schema.
    """
    subject_data: Dict[str, Any] = {
        "subject_code": "",
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
        "teaching_plan": []
    }

    # 1. Trích xuất Mã môn và Tên môn học từ tiêu đề hoặc tên thư mục
    code_match = re.search(r"(\d{6})", subject_folder_name)
    if code_match:
        subject_data["subject_code"] = code_match.group(1)

    name_vi_match = re.search(r"Tiếng Việt:\s*([^Tiếng|\n<]+)", md_content, re.IGNORECASE)
    if name_vi_match:
        subject_data["subject_name_vi"] = name_vi_match.group(1).strip()
    else:
        # Lấy từ tên thư mục
        subject_data["subject_name_vi"] = re.sub(r"^\d+[\s_-]*", "", subject_folder_name).split("-")[0].strip()

    name_en_match = re.search(r"Tiếng Anh:\s*([^Mã|\n<]+)", md_content, re.IGNORECASE)
    if name_en_match:
        subject_data["subject_name_en"] = name_en_match.group(1).strip()

    # 2. Mô tả học phần (Course Description)
    desc_match = re.search(r"(?:2\.\s*Mô tả tóm tắt học phần|Course description)(.*?)(?:3\.\s*Mục tiêu|Course Objectives)", md_content, re.DOTALL | re.IGNORECASE)
    if desc_match:
        subject_data["description"] = re.sub(r"^[#\s\d\.]+", "", desc_match.group(1)).strip()

    # 3. Mục tiêu học phần (COs)
    co_matches = re.findall(r"(CO\d+)\s*[:\.]?\s*([^\n\r]+)", md_content)
    seen_cos = set()
    for co_code, desc in co_matches:
        if co_code not in seen_cos:
            seen_cos.add(co_code)
            subject_data["course_objectives"].append({
                "co_code": co_code,
                "description": desc.strip("✓ ").strip()
            })

    # 4. Chuẩn đầu ra học phần (CLOs)
    clo_matches = re.findall(r"(CLO\d+)\s*[:\.]?\s*([^\n\r]+)", md_content)
    seen_clos = set()
    for clo_code, desc in clo_matches:
        if clo_code not in seen_clos:
            seen_clos.add(clo_code)
            subject_data["clos"].append({
                "clo_code": clo_code,
                "description": desc.strip("✓ ").strip()
            })

    # 5. Nhiệm vụ của sinh viên
    duties_match = re.search(r"(?:5\.\s*Nhiệm vụ của sinh viên|Students duties)(.*?)(?:6\.\s*Phương pháp|7\.\s*Kế hoạch)", md_content, re.DOTALL | re.IGNORECASE)
    if duties_match:
        duties_text = duties_match.group(1).strip()
        lines = [re.sub(r"^[\\\-\*\s]+", "", line).strip() for line in duties_text.split("\n") if line.strip()]
        subject_data["student_duties"] = [l for l in lines if len(l) > 5 and not l.startswith("#")]

    return subject_data


def process_all_subjects():
    """Duyệt qua tất cả các môn học đã được parse và trích xuất sang JSON"""
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "json_collections").mkdir(parents=True, exist_ok=True)

    subjects_list = []

    # Quét trong parsed_output
    if PARSED_OUTPUT_DIR.exists():
        for subject_dir in sorted(PARSED_OUTPUT_DIR.iterdir()):
            if subject_dir.is_dir():
                md_files = list(subject_dir.glob("**/*.md"))
                if md_files:
                    md_path = md_files[0]
                    with open(md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    print(f"[*] Đang trích xuất: {subject_dir.name}")
                    data = parse_subject_markdown(content, subject_dir.name)
                    subjects_list.append(data)

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(subjects_list, f, ensure_ascii=False, indent=2)

    print(f"\n[✓] Hoàn tất! Đã trích xuất {len(subjects_list)} môn học vào: {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    process_all_subjects()
