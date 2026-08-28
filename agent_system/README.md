# 🤖 Module Tác Tử Thông Minh (`agent_system`)

Thư mục này chứa **Hệ thống Tác tử Thông minh (Agentic AI Core)**, chịu trách nhiệm định tuyến ý định (Router), điều phối truy xuất tri thức (RAG Engine) và kiểm chứng câu trả lời (Verifier).

---

## 📂 1. Cấu trúc Thư mục

```plaintext
agent_system/
├── README.md                       # Tài liệu hướng dẫn module Tác tử
├── router.py                       # AI Router: Phân loại ý định & Trích xuất mã môn học
├── verifier.py                     # AI Verifier: Kiểm tra chéo điểm số & Hủy lọc môn nếu sai
├── app.py                          # Application Pipeline chính thức (End-to-End Chatbot)
├── test_router.py                  # Kiểm thử trực quan AI Router (Step 1)
└── test_app.py                     # Kiểm thử hệ thống Chatbot hoàn chỉnh
```

---

## 🚀 2. Hướng dẫn Chạy Kiểm thử Step-by-Step

### 🔹 Step 1: Kiểm thử AI Router
```bash
.venv/bin/python agent_system/test_router.py
```
