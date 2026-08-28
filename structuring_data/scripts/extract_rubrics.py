#!/usr/bin/env python3
"""
Script trích xuất Collection 'rubric_catalog.json' cho danh mục Rubric & Tiêu chí đánh giá.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_RUBRICS_PATH = BASE_DIR / "json_collections" / "rubric_catalog.json"


def build_rubric_catalog():
    """Tạo dữ liệu Danh mục Rubric và tiêu chí đánh giá môn học"""

    rubrics_data = [
        {
            "rubric_id": "RUBRIC_A1.1",
            "assessment_code": "A1.1",
            "assessment_name": "Đánh giá Chuyên cần & Điểm danh",
            "assessment_type": "process",
            "default_weight_percent": 10,
            "criteria": [
                {
                    "criterion_id": "CRIT_ATTENDANCE",
                    "name": "Mức độ tham dự lớp học",
                    "description": "Sinh viên tham dự tối thiểu 80% số tiết học trên lớp và tham gia phát biểu xây dựng bài.",
                    "weight_percent": 100
                }
            ]
        },
        {
            "rubric_id": "RUBRIC_A2.1",
            "assessment_code": "A2.1",
            "assessment_name": "Bài tập Thực hành & Bài tập tại lớp",
            "assessment_type": "process",
            "default_weight_percent": 20,
            "criteria": [
                {
                    "criterion_id": "CRIT_CODE_ACCURACY",
                    "name": "Độ chính xác của thuật toán và code",
                    "description": "Cài đặt thuật toán chính xác, chạy thành công các test case được giao.",
                    "weight_percent": 60
                },
                {
                    "criterion_id": "CRIT_CODE_STYLE",
                    "name": "Phong cách lập trình & Chuẩn Clean Code",
                    "description": "Mã nguồn rõ ràng, đặt tên biến chuẩn, có comment giải thích.",
                    "weight_percent": 40
                }
            ]
        },
        {
            "rubric_id": "RUBRIC_A5.1",
            "assessment_code": "A5.1",
            "assessment_name": "Đánh giá Bài tập lớn / Đồ án môn học",
            "assessment_type": "final_or_major",
            "default_weight_percent": 50,
            "criteria": [
                {
                    "criterion_id": "CRIT_PROJECT_REPORT",
                    "name": "Báo cáo nội dung đồ án",
                    "description": "Báo cáo trình bày đầy đủ các phần: Đặt vấn đề, Giải pháp, Thực nghiệm và Kết luận.",
                    "weight_percent": 40
                },
                {
                    "criterion_id": "CRIT_PROJECT_DEMO",
                    "name": "Chương trình Demo & Thuyết trình",
                    "description": "Demo sản phẩm chạy mượt mà, trả lời chính xác các câu hỏi phản biện của giáo viên.",
                    "weight_percent": 60
                }
            ]
        }
    ]

    OUTPUT_RUBRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_RUBRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(rubrics_data, f, ensure_ascii=False, indent=2)

    print(f"[✓] Hoàn tất! Đã trích xuất rubric_catalog.json vào: {OUTPUT_RUBRICS_PATH}")


if __name__ == "__main__":
    build_rubric_catalog()
