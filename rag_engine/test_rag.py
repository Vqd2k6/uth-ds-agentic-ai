#!/usr/bin/env python3
"""
Kịch bản kiểm thử RAG Engine tương tác từ Terminal.
"""

import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from pipeline import RAGEngine


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử RAG Engine (Hybrid Search + GraphRAG)")
    parser.add_argument("--query", "-q", type=str, help="Câu hỏi kiểm thử")
    parser.add_argument("--subject", "-s", type=str, default="124100", help="Mã môn học (mặc định 124100)")
    args = parser.parse_args()

    engine = RAGEngine()

    query_text = args.query or "Học phần Lập trình Python trang bị những kiến thức nào ở CLO1?"
    
    result = engine.query(query_text, subject_code=args.subject)
    
    print("\n" + "=" * 65)
    print("📋 KẾT QUẢ TRUY XUẤT NGỮ CẢNH HOÀN CHỈNH CHO LLM AGENT:")
    print("=" * 65)
    print(result["formatted_context"])
    print("=" * 65)

    engine.close()


if __name__ == "__main__":
    main()
