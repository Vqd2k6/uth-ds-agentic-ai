# 🗄️ Module Nạp Dữ Liệu Cơ Sở Dữ Liệu (`database_ingestion`)

Thư mục này chịu trách nhiệm **khởi tạo hạ tầng Cơ sở Dữ liệu và nạp 4 bộ JSON Collections** từ `structuring_data/json_collections/` vào **MongoDB**, **Qdrant Vector DB** và **Neo4j Knowledge Graph**.

---

## 📂 1. Cấu trúc Thư mục

```plaintext
database_ingestion/
├── README.md                       # Tài liệu hướng dẫn module nạp dữ liệu
├── docker-compose.yml              # File cấu hình Docker khởi chạy 3 Database
├── config.py                       # Thông số cấu hình kết nối CSDL (Mongo, Qdrant, Neo4j)
├── scripts/                        # Kịch bản nạp dữ liệu từng CSDL
│   ├── ingest_mongodb.py           # Nạp 4 JSON Collections vào MongoDB
│   ├── ingest_qdrant.py            # Embeddings & nạp chunk_sources vào Qdrant
│   ├── ingest_neo4j.py             # Dựng Đồ thị tri thức (Môn - CLO - PLO) trên Neo4j
│   └── seed_all.py                 # Kịch bản tổng nạp dữ liệu vào cả 3 CSDL cùng lúc
└── requirements.txt                # Thư viện Python phục vụ kết nối CSDL
```

---

## 🛠️ 2. Lộ trình Triển khai Step-by-Step

| Bước | Nội dung công việc | Trạng thái |
| :--- | :--- | :--- |
| **Bước 1** | **Khởi tạo Hạ tầng Docker** (`docker-compose.yml` tích hợp Mongo, Qdrant, Neo4j) | ✅ Hoàn thành |
| **Bước 2** | **Kịch bản Nạp dữ liệu MongoDB** (`ingest_mongodb.py` nạp 4 JSON Collections) | ✅ Hoàn thành |
| **Bước 3** | **Kịch bản Nạp Vector DB Qdrant** (`ingest_qdrant.py` với Nomic Embeddings + BM25) | ⏳ Tiếp theo |
| **Bước 4** | **Kịch bản Dựng Graph Neo4j** (`ingest_neo4j.py` kết nối Môn học ↔ CLO ↔ PLO) | ⏳ Tiếp theo |
| **Bước 5** | **Kịch bản Tổng hợp Nạp tự động** (`seed_all.py` & Kiểm thử truy vấn RAG) | ⏳ Tiếp theo |

---

## 🍃 3. Hướng dẫn Chạy Kịch bản Nạp dữ liệu MongoDB (Bước 2)

Khởi chạy kịch bản nạp 4 bộ JSON Collections vào MongoDB:
```bash
.venv/bin/python database_ingestion/scripts/ingest_mongodb.py
```
*Script hỗ trợ cả chế độ nạp trực tiếp vào MongoDB Server và chế độ Kiểm thử Cấu trúc (Dry-run Mode).*
