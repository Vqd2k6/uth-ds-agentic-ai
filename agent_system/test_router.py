#!/usr/bin/env python3
"""
Script Kiểm thử Trực quan AI Router (Bộ định tuyến ý định).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from router import AIRouter


def main():
    router = AIRouter()

    test_cases = [
        "Môn Lập trình Python trang bị những kiến thức gì ở CLO1?",
        "Điểm bài tập lớn môn 124100 tính thế nào?",
        "Học phần nào dạy về Học máy và phân tích dữ liệu?",
        "Môn toán cho máy có mấy tín chỉ?",
        "Xin chào bạn, bạn là ai?"
    ]

    print("\n" + "=" * 70)
    print("📊 BẢNG KẾT QUẢ PHÂN TÍCH AI ROUTER (STEP 1 TEST)")
    print("=" * 70)
    print(f"{'CÂU HỎI ĐẦU VÀO':<45} | {'INTENT':<16} | {'MÔN':<8} | {'CONFIDENCE':<10} | {'QUYẾT ĐỊNH RAG'}")
    print("-" * 105)

    for query in test_cases:
        res = router.route(query)
        subj = res['final_subject_code'] if res['final_subject_code'] else "None"
        decision = f"Lọc môn {subj}" if not res['use_global_search'] else "Duyệt Toàn Cục"
        conf_str = f"{res['confidence_score'] * 100:.0f}%"
        print(f"{query[:44]:<45} | {res['intent']:<16} | {subj:<8} | {conf_str:<10} | {decision}")

    print("=" * 105 + "\n")


if __name__ == "__main__":
    main()
