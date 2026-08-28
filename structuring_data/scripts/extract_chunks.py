#!/usr/bin/env python3
"""
Script trích xuất Collection 'chunk_sources' từ Đề cương chi tiết học phần.
Phân rã văn bản thành các đoạn (chunks) nguyên tử phục vụ Qdrant Vector DB & BM25 Search.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
SUBJECTS_JSON_PATH = BASE_DIR / "json_collections" / "syllabus_subjects.json"
OUTPUT_CHUNKS_PATH = BASE_DIR / "json_collections" / "chunk_sources.json"


def build_chunks_from_subjects():
    """Tạo ra các chunks nguyên tử từ dữ liệu syllabus_subjects.json"""
    if not SUBJECTS_JSON_PATH.exists():
        print(f"[!] Không tìm thấy {SUBJECTS_JSON_PATH}. Vui lòng chạy extract_subjects.py trước!")
        return

    with open(SUBJECTS_JSON_PATH, "r", encoding="utf-8") as f:
        subjects = json.load(f)

    all_chunks: List[Dict[str, Any]] = []

    for subject in subjects:
        code = subject.get("subject_code", "UNKNOWN")
        name_vi = subject.get("subject_name_vi", "")

        # 1. Chunk Mô tả học phần
        if subject.get("description"):
            all_chunks.append({
                "chunk_id": f"{code}_description",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "description",
                "section_title": "2. Mô tả tóm tắt học phần",
                "content": f"Mô tả môn học {name_vi} ({code}): {subject['description']}",
                "metadata": {"subject_code": code}
            })

        # 2. Chunks Mục tiêu môn học (COs)
        for idx, co in enumerate(subject.get("course_objectives", []), 1):
            all_chunks.append({
                "chunk_id": f"{code}_co_{co['co_code'].lower()}",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "course_objective",
                "section_title": "3. Mục tiêu học phần (CO)",
                "content": f"Mục tiêu {co['co_code']} môn {name_vi}: {co['description']}",
                "metadata": {"subject_code": code, "co_code": co["co_code"]}
            })

        # 3. Chunks Chuẩn đầu ra môn học (CLOs)
        for idx, clo in enumerate(subject.get("clos", []), 1):
            all_chunks.append({
                "chunk_id": f"{code}_clo_{clo['clo_code'].lower()}",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "clo",
                "section_title": "4. Chuẩn đầu ra học phần (CLO)",
                "content": f"Chuẩn đầu ra {clo['clo_code']} môn {name_vi}: {clo['description']}",
                "metadata": {"subject_code": code, "clo_code": clo["clo_code"]}
            })

        # 4. Chunk Nhiệm vụ sinh viên
        if subject.get("student_duties"):
            duties_str = "\n- " + "\n- ".join(subject["student_duties"])
            all_chunks.append({
                "chunk_id": f"{code}_student_duties",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "student_duties",
                "section_title": "5. Nhiệm vụ của sinh viên",
                "content": f"Nhiệm vụ của sinh viên khi học môn {name_vi}:{duties_str}",
                "metadata": {"subject_code": code}
            })

    with open(OUTPUT_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"[✓] Hoàn tất! Đã sinh ra {len(all_chunks)} chunks vào: {OUTPUT_CHUNKS_PATH}")


if __name__ == "__main__":
    build_chunks_from_subjects()
