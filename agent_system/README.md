# 🤖 Module Tác Tử Thông Minh (`agent_system`)

Thư mục này chứa **Hệ thống Tác tử Thông minh (Agentic AI Core)**, chịu trách nhiệm định tuyến ý định (Router), điều phối truy xuất tri thức (RAG Engine), kiểm chứng câu trả lời (Verifier) và tạo phản hồi hoàn chỉnh cho sinh viên.

---

## 📂 1. Cấu trúc Thư mục

```plaintext
agent_system/
├── README.md                       # Tài liệu hướng dẫn module Tác tử
├── router.py                       # AI Router: Phân loại ý định & Trích xuất mã môn học
├── verifier.py                     # AI Verifier: Kiểm tra chéo điểm số & Hủy lọc môn nếu sai
├── app.py                          # Master Agent System Pipeline (End-to-End Chatbot)
├── test_router.py                  # Kiểm thử trực quan AI Router (Step 1)
├── test_verifier.py                # Kiểm thử AI Verifier & Cơ chế sửa sai (Step 2)
└── test_app.py                     # Kiểm thử toàn bộ hệ thống Chatbot End-to-End (Step 3 & 4)
```

---

## 🚀 2. Hướng dẫn Chạy Kiểm thử Step-by-Step

### 🔹 Step 1: Kiểm thử AI Router (Phân loại Ý định & Điểm tin cậy)
```bash
.venv/bin/python agent_system/test_router.py
```

### 🔹 Step 2: Kiểm thử AI Verifier (Cơ chế Tự động Sửa sai)
```bash
.venv/bin/python agent_system/test_verifier.py
```

### 🔹 Step 3 & 4: Kiểm thử Hệ thống Chatbot Agent System hoàn chỉnh (End-to-End)
```bash
.venv/bin/python agent_system/test_app.py --query "Môn Lập trình Python học tuần mấy và CLO1 gồm những gì?"
```
