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
│   ├── ingest_qdrant.py            # Nomic Embeddings (768-dim) & nạp chunk_sources vào Qdrant
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
| **Bước 3** | **Kịch bản Nạp Vector DB Qdrant** (`ingest_qdrant.py` với Nomic Embeddings 768-dim) | ✅ Hoàn thành |
| **Bước 4** | **Kịch bản Dựng Graph Neo4j** (`ingest_neo4j.py` kết nối Môn học ↔ CLO ↔ PLO) | ✅ Hoàn thành |
| **Bước 5** | **Kịch bản Tổng hợp Nạp tự động** (`seed_all.py` nạp tự động vào cả 3 CSDL) | ✅ Hoàn thành |

---

## 🚀 3. Hướng dẫn Chạy Kịch bản Nạp dữ liệu

### 🔹 3.1. Chạy toàn bộ Pipeline Nạp tự động vào 3 CSDL (Khuyên dùng)
```bash
.venv/bin/python database_ingestion/scripts/seed_all.py
```

### 🔹 3.2. Chạy từng kịch bản đơn lẻ
```bash
# 1. Nạp MongoDB Document Store
.venv/bin/python database_ingestion/scripts/ingest_mongodb.py

# 2. Vector hóa Nomic & Nạp Qdrant Vector DB
.venv/bin/python database_ingestion/scripts/ingest_qdrant.py

# 3. Dựng Đồ thị Tri thức trên Neo4j
.venv/bin/python database_ingestion/scripts/ingest_neo4j.py
```
*Tất cả các script đều hỗ trợ cơ chế tự động chuyển sang chế độ Kiểm thử (Dry-run Mode) giúp bạn chạy kiểm định ngay cả khi chưa bật CSDL.*
