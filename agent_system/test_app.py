#!/usr/bin/env python3
"""
Script Kiểm thử Trực quan Hệ thống Chatbot Agent System hoàn chỉnh (Step 3 & 4 Test).
"""

import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from app import AgentSystemApp


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử Hệ thống Agent System Chatbot")
    parser.add_argument("--query", "-q", type=str, help="Câu hỏi từ sinh viên")
    args = parser.parse_args()

    app = AgentSystemApp()

    default_queries = [
        "Lập trình Python cơ bản gồm những kiến thức gì?",
        "Học phần nào dạy về thư viện Pandas và xử lý dữ liệu?",
        "Xin chào bạn, bạn có thể giúp gì cho tôi?"
    ]

    queries = [args.query] if args.query else default_queries

    print("\n" + "=" * 75)
    print("🤖 THỬ NGHIỆM HỆ THỐNG AGENT SYSTEM CHATBOT HOÀN CHỈNH")
    print("=" * 75)

    for idx, q in enumerate(queries, 1):
        res = app.chat(q)
        print(f"\n💬 [PHẢN HỒI AGENT - CÂU {idx}]:")
        print("-" * 65)
        print(res["final_answer"])
        print("-" * 65)

    print("=" * 75 + "\n")
    app.close()


if __name__ == "__main__":
    main()
