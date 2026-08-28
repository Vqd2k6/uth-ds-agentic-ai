# 🧩 Module Chuẩn Hóa Dữ Liệu Schema & Chunking (`structuring_data`)

Thư mục này chịu trách nhiệm **chuyển đổi dữ liệu đã bóc tách từ Markdown (`.md`) và `_content_list.json`** trong `preprocessing_data/parsed_output/` thành **4 tập dữ liệu JSON Collection chuẩn hóa** sẵn sàng lưu vào **MongoDB**, **Neo4j** và **Qdrant Vector Database**.

---

## 📂 1. Cấu trúc Thư mục

```plaintext
structuring_data/
├── README.md                       # Tài liệu hướng dẫn module chuẩn hóa dữ liệu
├── scripts/                        # Các kịch bản Python thực hiện bóc tách Schema
│   ├── extract_subjects.py         # Trích xuất collection syllabus_subjects (ĐCCT chi tiết)
│   ├── extract_frameworks.py       # Trích xuất collection outcome_frameworks (Khung PLO toàn ngành)
│   ├── extract_rubrics.py          # Trích xuất collection rubric_catalog (Tiêu chí chấm điểm)
│   ├── extract_chunks.py           # Cắt nhỏ văn bản thành chunk_sources cho Vector DB
│   └── run_all_structuring.py      # Kịch bản tổng điều phối chạy toàn bộ pipeline
└── json_collections/               # Kết quả 4 bộ dữ liệu JSON Collection đã chuẩn hóa
    ├── syllabus_subjects.json
    ├── outcome_frameworks.json
    ├── rubric_catalog.json
    └── chunk_sources.json
```

---

## 📊 2. Quy hoạch 4 Collections Đầu Ra

### 1️⃣ `syllabus_subjects.json` (Thông tin Chi tiết Đề cương Học phần)
- **Mục đích**: Lưu trữ thông tin tổng quan môn học, danh sách mục tiêu ($CO$), chuẩn đầu ra ($CLO$), học phần tiên quyết/học trước và chi tiết kế hoạch 15 tuần học.
- **Ứng dụng**: Phục vụ câu hỏi chi tiết về nội dung môn học, tuần học.

### 2️⃣ `outcome_frameworks.json` (Khung Chuẩn Đầu Ra Ngành & Ma Trận Đóng Góp)
- **Mục đích**: Lưu trữ khung chuẩn đầu ra toàn ngành KHDL (PO1-PO5, PLO1-PLO7) và ma trận mức độ đóng góp (`I`, `R`, `M`, `A`) của từng môn học vào PLO.
- **Ứng dụng**: Phục vụ **AI Router & AI Plan** tư vấn lộ trình học tập toàn khóa và xây dựng Đồ thị tri thức trên **Neo4j**.

### 3️⃣ `rubric_catalog.json` (Danh mục Rubric & Tiêu chí Đánh giá)
- **Mục đích**: Lưu trữ chi tiết phương pháp đánh giá (A1.1 chuyên cần, A2.1 bài tập lớp, A5.1 bài tập lớn) và phần trăm trọng số điểm.
- **Ứng dụng**: Giải đáp thắc mắc về quy chế thi, cách tính điểm và tiêu chí chấm bài.

### 4️⃣ `chunk_sources.json` (Tập Tri thức Nguyên tử cho Vector DB RAG)
- **Mục đích**: Phân rã nhỏ nội dung thành các Chunks ngắn (200 - 500 từ) kèm đầy đủ Metadata (Mã môn, Tuần, CLO).
- **Ứng dụng**: Nạp trực tiếp vào **Qdrant Vector DB** và **BM25** phục vụ truy vấn ngữ nghĩa cực nhanh cho RAG.

---

## 🚀 3. Hướng dẫn Chạy Pipeline Chuẩn Hóa

### 🔹 3.1. Chạy toàn bộ Pipeline chuẩn hóa dữ liệu
```bash
.venv/bin/python structuring_data/scripts/run_all_structuring.py
```

### 🔹 3.2. Chạy từng kịch bản đơn lẻ
```bash
# 1. Trích xuất thông tin môn học sang syllabus_subjects.json
.venv/bin/python structuring_data/scripts/extract_subjects.py

# 2. Sinh tập Chunks cho Vector DB sang chunk_sources.json
.venv/bin/python structuring_data/scripts/extract_chunks.py
```
