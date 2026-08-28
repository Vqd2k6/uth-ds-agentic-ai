# 🔍 Module Tra Cứu Tri Thức Lai & Đồ Thị (`rag_engine`)

Thư mục này chịu trách nhiệm **truy xuất tri thức đa phương thức (Hybrid RAG + GraphRAG)**, kết hợp giữa:
1. **Dense Vector Search (Qdrant)**: Tìm kiếm ngữ nghĩa bằng mô hình `Nomic-Embed-Text v1.5` (768 chiều).
2. **Sparse Keyword Search (BM25)**: Tìm kiếm từ khóa chính xác (mã môn, thuật ngữ chuyên ngành).
3. **Reciprocal Rank Fusion (RRF)**: Thuật toán hợp nhất xếp hạng giữa Dense & Sparse Search.
4. **Knowledge Graph Search (Neo4j)**: Truy vấn đường đi quan hệ Đồ thị tri thức (Course $\rightarrow$ CLO $\rightarrow$ PLO).

---

## 📂 1. Cấu trúc Thư mục

```plaintext
rag_engine/
├── README.md                       # Tài liệu hướng dẫn module RAG Engine
├── retrievers/                     # Các bộ công cụ truy xuất tri thức
│   ├── dense_retriever.py          # Tìm kiếm Vector ngữ nghĩa trên Qdrant
│   ├── sparse_retriever.py         # Tìm kiếm từ khóa chính xác bằng BM25
│   ├── hybrid_retriever.py         # Hợp nhất xếp hạng RRF giữa Dense + Sparse
│   └── graph_retriever.py          # Truy vấn Đồ thị tri thức trên Neo4j
├── pipeline.py                     # Pipeline điều phối truy xuất tri thức tổng hợp
└── test_rag.py                     # Kịch bản kiểm thử truy vấn RAG tương tác từ Terminal
```

---

## 🚀 2. Hướng dẫn Chạy Kiểm thử RAG Engine

### 🔹 Kiểm thử truy vấn tìm kiếm lai (Hybrid Search & Graph Search)
```bash
.venv/bin/python rag_engine/test_rag.py --query "Học phần Lập trình Python trang bị những kiến thức nào ở CLO1?"
```
