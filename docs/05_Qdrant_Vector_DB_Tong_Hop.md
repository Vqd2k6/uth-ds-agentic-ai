# Tổng quan về Qdrant Vector Database & Cơ chế Chỉ mục HNSW

**Qdrant** là một Vector Database Engine hiệu năng cao viết bằng ngôn ngữ Rust, được thiết kế chuyên biệt để lưu trữ, quản lý và tìm kiếm các tập dữ liệu vectơ đa chiều khổng lồ với độ trễ thấp ở mức mili-giây.

---

## 1. Các Khái niệm Cốt lõi trong Qdrant

### A. Point (Điểm dữ liệu)
Đơn vị lưu trữ cơ bản trong Qdrant, tương đương với một Row trong RDBMS hoặc một Document trong MongoDB. Một **Point** gồm 3 phần chính:
1. **ID**: Định danh duy nhất (Integer hoặc UUID).
2. **Vectors**: Tọa độ biểu diễn trong không gian (chứa cả Dense Vector và Sparse Vector).
3. **Payload**: Dữ liệu JSON chứa văn bản gốc và các trường metadata bổ sung (Category, Code, Author...).

---

### B. Giải thích Chi tiết Cấu trúc 1 Point trong Qdrant

Dưới đây là hình dung thực tế về 1 Point (Tài liệu $d_1$ quy chế UTH) được lưu trữ bên trong Qdrant Vector Engine:

```json
{
  "id": 1,
  "vector": {
    "dense-nomic": [0.85, 0.12, 0.91, 0.05, "... (768 chiều float32)"],
    "sparse-bm25": {
      "indices": [102, 405, 891],
      "values": [0.4700, 0.4700, 1.2743]
    }
  },
  "payload": {
    "text": "Sinh viên UTH cần hoàn thành tối thiểu 130 tín chỉ để ra trường.",
    "category": "Quy chế đào tạo",
    "code": "REG_UTH_130",
    "created_at": "2026-08-04"
  }
}
```

---

### C. Nguồn gốc từng Trường dữ liệu (Nó có được bằng cách nào?)

Để tạo ra được 1 Point JSON như trên, mã nguồn Python (`qdrant_service.py`) đã thu thập dữ liệu từ 3 nguồn khác nhau trong Pipeline:

```
[Văn bản thô & Metadata] ───────────────► Nạp thẳng vào ──► "payload"
                                                                │
[Mô hình Nomic MoE v2] ──► Embed 768-D ─► Nạp vào ────────► "dense-nomic"
                                                                │
[Mô hình FastEmbed BM25] ─► FastEmbed ──► Nạp vào ────────► "sparse-bm25"
                                                                │
                                                                ▼
                                                   [TẠO NÊN 1 POINT HOÀN CHỈNH]
```

---

## 2. Cơ chế Chỉ mục HNSW Graph (Hierarchical Navigable Small World)

### A. Đặt bài toán: Tại sao cần HNSW?
Giả sử Qdrant lưu trữ **1.000.000 Dense Vectors** bài viết và tài liệu UTH:
* **Cách ngây thơ (Flat Search / Brute-force)**: Khi có câu hỏi, máy tính phải đi tính điểm Cosine với **lần lượt cả 1 triệu vector** $\Rightarrow$ Mất vài giây cho 1 truy vấn (Độ phức tạp $O(N)$ - Quá chậm!).
* **Cách HNSW**: Chỉ cần tính điểm với khoảng **20 - 50 vector tiêu biểu** qua đồ thị là tìm ra ngay các vector gần nhất với độ chính xác 99% chỉ trong **0.001 giây** (Độ phức tạp $O(\log N)$).

---

### B. Ví dụ Thực tế Gắn với Cấu trúc Dữ liệu UTH
Giả sử bạn đang tìm kiếm **"Đề cương chi tiết học phần Đại số Tuyến tính (MATH1201)"** trong toàn bộ kho tài liệu hàng triệu văn bản của Trường UTH. 

Thay vì quét duyệt từng trang văn bản (Brute-force), HNSW tự động di chuyển qua **3 tầng Đồ thị Phân cấp UTH**:

```
[ Layer 2: Khối Kiến thức Lớn ]  Khung Chương trình ────────────────► Đề cương Học phần UTH
                                                                             │
[ Layer 1: Bộ môn Chuyên môn ]   ... ─────────────────► Khoa CNTT ────► Bộ môn Toán Cơ bản
                                                                             │
[ Layer 0: Tài liệu Chi tiết ]   ... ─────────────────► Đề cương MATH1201 (Tìm thấy!)
```

1. **Layer 2 (Tầng Khối Kiến thức Lớn - Nhảy khoảng cách xa)**:
   * Từ vị trí bắt đầu, câu hỏi nhảy ngay tới Nút đại diện cho **[Khối Đề cương Chi tiết Học phần]** (Bỏ qua hoàn toàn hàng triệu văn bản thuộc Khối Quy chế Đào tạo, Khối Tin tức Nghỉ lễ, Khối Hành chính).
2. **Layer 1 (Tầng Bộ môn Chuyên môn - Nhảy khoảng cách trung bình)**:
   * Từ Khối Đề cương, di chuyển tới Nút đại diện cho **[Bộ môn Toán - Khoa CNTT UTH]**.
3. **Layer 0 (Tầng Văn bản Chi tiết - Nhảy bước ngắn)**:
   * Tại Bộ môn Toán, dò theo các đường nối để tới đúng Nút văn bản: **`"Môn học Đại số Tuyến tính (MATH1201) trang bị kiến thức..."`**.

---

### C. Nguyên lý Hoạt động của HNSW trong Qdrant Vector Engine

HNSW xây dựng một mạng lưới Đồ thị Phân cấp (Multi-layer Graph) nối các Vector tài liệu UTH lại với nhau dựa trên sự tương đồng tọa độ:

```
 [ Layer 2 - Thưa nhất ] ───►  Node A ──────────────────► Node F (Bay nhanh tới khối UTH)
                                 │                         │
 [ Layer 1 - Trung bình ] ──►  Node A ──────► Node C ─────► Node F (Thu hẹp Bộ môn)
                                 │             │           │
 [ Layer 0 - Dày đặc nhất] ─► Node A ─► Node B ─► Node C ─► Node D ─► Node E ─► Node F
```

1. **Quá trình Xây dựng Đồ thị (Index Phase)**: Mỗi khi nạp 1 Point mới vào Qdrant, HNSW tự động tính toán vị trí địa lý của nó và bắn dây liên kết ($M$ Edges) với các Nút tài liệu UTH nằm gần nó nhất.
2. **Quá trình Truy vấn (Search Phase)**:
   * Thả Vector câu hỏi vào Layer 2 $\rightarrow$ Tìm Nút gần nhất ở tầng này.
   * "Tụt" xuống Layer 1 $\rightarrow$ Nhảy qua các Nút Bộ môn lân cận để áp sát vị trí câu hỏi.
   * "Tụt" xuống Layer 0 $\rightarrow$ Dò từng bước ngắn để rút ra đúng **Top K Vector gần nhất**.
3. **Độ phức tạp $O(\log N)$**: Nhờ cơ chế "nhảy tầng", với 1.000.000 tài liệu UTH, HNSW chỉ mất khoảng $\log_2(1.000.000) \approx 20$ nấc chuyển là ra kết quả!

---

## 3. Qdrant Native Hybrid Search & Prefetching

Qdrant hỗ trợ cơ chế **Prefetching** cho phép thực thi đa luồng truy vấn song song ở cấp C++ Engine trước khi kết hợp bằng RRF:

```
                      ┌─────────────────────────────────┐
                      │    QDRANT ENGINE PREFETCH       │
                      └────────────────┬────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌───────────────────────────┐                         ┌───────────────────────────┐
│     LUỒNG 1: DENSE        │                         │     LUỒNG 2: SPARSE       │
│   (nomic-embed-text-moe)  │                         │          (BM25)           │
│   Lấy Top 10 Candidates   │                         │   Lấy Top 10 Candidates   │
└───────────┬───────────────┘                         └───────────┬───────────────┘
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                      ┌─────────────────────────────────┐
                      │    NATIVE RRF FUSION ENGINE     │
                      │  models.FusionQuery(Fusion.RRF) │
                      └────────────────┬────────────────┘
                                       ▼
                      ┌─────────────────────────────────┐
                      │      TOP K FINAL RESULTS        │
                      └─────────────────────────────────┘
```
