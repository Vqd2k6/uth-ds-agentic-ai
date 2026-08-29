#!/usr/bin/env python3
"""
Script Kiểm thử Trực quan AI Verifier & Cơ chế Tự động Sửa sai (Step 2 Test).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from verifier import AIVerifier


def main():
    verifier = AIVerifier()

    print("\n" + "=" * 75)
    print("🧪 KIỂM THỬ THỰC TẾ: AI VERIFIER TỰ ĐỘNG SỬA SAI KHI ROUTER ĐOÁN NHẦM MÔN")
    print("=" * 75)

    # 1. Tình huống Router đoán đúng môn
    correct_case = {
        "query": "Lập trình Python cơ bản gồm kiến thức gì?",
        "final_subject_code": "124100", # Đúng môn Python
        "use_global_search": False
    }

    # 2. Tình huống Router ĐOÁN SAI MÔN (Hỏi Python nhưng phán nhầm môn 121000)
    wrong_case = {
        "query": "Lập trình Python cơ bản gồm kiến thức gì?",
        "final_subject_code": "121000", # CỐ TÌNH ĐOÁN SAI MÔN!
        "use_global_search": False
    }

    for idx, case in enumerate([correct_case, wrong_case], 1):
        print(f"\n📌 THỬ NGHIỆM {idx}: Query = '{case['query']}'")
        print(f"  - Giả lập Router đính mã môn: {case['final_subject_code']}")
        
        res = verifier.verify_and_retrieve(case)
        
        print(f"\n  [✓] Trạng thái Verifier:   {res['verification_status']}")
        print(f"  [✓] Tự động sửa sai:       {' CÓ (Hủy lọc môn -> Duyệt toàn cục)' if res['is_fallback_triggered'] else '❌ KHÔNG (Giữ nguyên lọc môn)'}")
        print(f"  [✓] Số đoạn tri thức tìm thấy: {len(res['final_chunks'])} chunks")

    print("\n" + "=" * 75)
    verifier.close()


if __name__ == "__main__":
    main()
