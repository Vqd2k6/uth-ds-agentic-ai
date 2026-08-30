#!/usr/bin/env python3
"""
Script Kiểm thử Trực quan Hệ thống Chatbot Agent System hoàn chỉnh (Local Open-Source LLM).
Hỗ trợ kiểm thử câu hỏi đơn lẻ hoặc Chế độ Hội thoại Tương tác Trực tiếp (Interactive Mode).
"""

import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
from app import AgentSystemApp


def main():
    parser = argparse.ArgumentParser(description="Kiểm thử Hệ thống Agent System Chatbot với Local LLM")
    parser.add_argument("--query", "-q", type=str, help="Câu hỏi từ sinh viên")
    parser.add_argument("--model", "-m", type=str, default="qwen2.5:3b", help="Tên mô hình Ollama (mặc định: qwen2.5:3b)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Kích hoạt chế độ trò chuyện tương tác liên tục")
    args = parser.parse_args()

    app = AgentSystemApp(model_name=args.model)

    if args.interactive:
        print("\n" + "=" * 75)
        print(f"🎓 CHATBOT CỐ VẤN HỌC TẬP KHOA HỌC DỮ LIỆU (UTH) - MODEL: {args.model}")
        print("💡 Gõ 'exit' hoặc 'quit' để kết thúc chương trình.")
        print("=" * 75)

        while True:
            try:
                user_input = input("\n👨‍🎓 Sinh viên: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\n👋 Tạm biệt bạn! Chúc bạn học tập tốt tại UTH.\n")
                    break

                res = app.chat(user_input)
                print("\n🤖 Trợ lý AI Cố vấn:")
                print("-" * 65)
                print(res["final_answer"])
                print("-" * 65)

            except KeyboardInterrupt:
                print("\n\n👋 Tạm biệt bạn!\n")
                break
        app.close()
        return

    default_queries = [
        "Lập trình Python cơ bản gồm những kiến thức gì?",
        "Học phần Lập trình Python học tuần mấy và CLO1 gồm những gì?",
        "Xin chào bạn, bạn có thể giúp gì cho tôi?"
    ]

    queries = [args.query] if args.query else default_queries

    print("\n" + "=" * 75)
    print(f"🤖 THỬ NGHIỆM HỆ THỐNG AGENT SYSTEM VỚI LOCAL LLM ({args.model})")
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
