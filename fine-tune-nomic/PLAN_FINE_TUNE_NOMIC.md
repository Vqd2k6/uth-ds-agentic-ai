# Kế hoạch Chi tiết: Fine-Tuning Nomic MoE v2 & Tích hợp Qdrant Hybrid Search

Tài liệu này trình bày lộ trình kỹ thuật toàn diện để thực hiện Fine-Tuning mô hình **Nomic Embed Text MoE v2** (`nomic-ai/nomic-embed-text-v2-moe`) trên bộ dữ liệu đề cương 41 học phần thực tế của Trường ĐH Giao thông Vận tải TP.HCM (UTH) tại thư mục `output/`, lưu giữ tại thư mục `fine-tune-nomic/`.

---

## 1. Cấu trúc Thư mục Dự án `fine-tune-nomic/`

```
fine-tune-nomic/
├── PLAN_FINE_TUNE_NOMIC.md     # Kế hoạch thực hiện chi tiết
├── requirements.txt            # Các phụ thuộc (torch, sentence-transformers, peft, datasets, accelerate)
├── 02_train_nomic_colab.py     # Script huấn luyện tối ưu hóa cho Colab GPU T4 (fp16, batch size 32)
├── 03_evaluate_model.py        # Script đo lường chỉ số NDCG@10 & MRR@10 trên final_val_set.jsonl
├── train_nomic_colab.ipynb     # File Jupyter Notebook chạy trực tiếp 1-click trên Google Colab
└── checkpoints/                # Thư mục xuất weights mô hình đã fine-tune (uth-nomic-embed-v2)
```

---

## 2. Các Giai đoạn Thực hiện (Phases & Steps)

### Phase 1: Chuẩn bị Dữ liệu & Phân rã Chunks (Data Ingestion & Dataset Preparation)
* **File chính**: `fine-tune-nomic/01_prepare_dataset.py`
* **Nguồn dữ liệu**: 41 thư mục học phần thực tế trong `output/` (`.md` & `_content_list.json`).
* **Các bước kỹ thuật**:
  1. **Chunking**: Trích xuất các đoạn văn bản đề cương chi tiết (kích thước 300 - 500 từ), giữ nguyên cấu trúc Tiêu đề, Mã HP, Chuẩn đầu ra (CLO/PLO), Rubric.
  2. **Tạo Cặp Dữ liệu Huấn luyện (Synthetic Pair Generation)**:
     * Sử dụng quy tắc trích xuất Heuristic kết hợp LLM Prompting để biến mỗi Chunk văn bản thành cặp `(Query sinh viên, Positive Chunk)`.
     * *Ví dụ:*
       * `Query`: `"search_query: Mã học phần COMP3402 giảng dạy những nội dung gì?"`
       * `Positive Doc`: `"search_document: Học phần Xử lý Ngôn ngữ Tự nhiên (COMP3402) giảng dạy về Tokenization, Embeddings, Transformer và RAG."`
  3. **Phân chia Train/Test Split**: Chia 80% cho `train_pairs.json` và 20% cho `test_pairs.json`.

---

### Phase 2: Khởi tạo & Huấn luyện LoRA Fine-Tuning (Model Fine-Tuning Execution)
* **File chính**: `fine-tune-nomic/02_train_nomic_lora.py`
* **Mô hình gốc**: `nomic-ai/nomic-embed-text-v2-moe` (truyền `trust_remote_code=True`).
* **Các bước kỹ thuật**:
  1. **Tối ưu hóa Tài nguyên GPU (LoRA - Low-Rank Adaptation)**:
     * Đóng băng (Freeze) toàn bộ trọng số gốc 475M tham số của Nomic MoE.
     * Thêm ma trận thích ứng LoRA (Target Modules: `query`, `key`, `value`, `dense`) với $r=16, \alpha=32$. Giúp huấn luyện mượt mà trên GPU RTX 3090/4090/T4.
  2. **Cấu hình Loss Function**: Sử dụng `MultipleNegativesRankingLoss` (InfoNCE). Hàm loss này tự động lấy tất cả các tài liệu khác trong cùng Batch làm Negative samples (mẫu sai đối chứng).
  3. **Cấu hình Siêu tham số (Hyperparameters)**:
     * Learning Rate ($lr$): $2 \times 10^{-5}$ (tốc độ học nhỏ để bảo vệ tri thức gốc).
     * Batch Size: 16 hoặc 32 (tùy dung lượng VRAM GPU).
     * Epochs: 3 - 5 vòng lặp.
     * Warmup Ratio: 10% số steps.
  4. **Xuất Checkpoint**: Lưu mô hình hoàn thiện tại `fine-tune-nomic/checkpoints/uth-nomic-embed-v2`.

---

### Phase 3: Đánh giá & So sánh Kiểm chứng (Model Evaluation & Benchmarking)
* **File chính**: `fine-tune-nomic/03_evaluate_model.py`
* **Chỉ số đánh giá**:
  * **MRR@10 (Mean Reciprocal Rank)**: Tỉ lệ vị trí xuất hiện của tài liệu đúng trong Top 10.
  * **NDCG@10 (Normalized Discounted Cumulative Gain)**: Điểm chất lượng xếp hạng tổng thể.
* **Quy trình kiểm thử**:
  * Chạy đánh giá tập `test_pairs.json` trên **Mô hình Nomic Gốc**.
  * Chạy đánh giá tập `test_pairs.json` trên **Mô hình Nomic Fine-tuned (`uth-nomic-embed-v2`)**.
  * Xuất báo cáo so sánh mức độ cải thiện (Kỳ vọng tăng 15% - 30% độ chính xác).

---

### Phase 4: Tích hợp vào Qdrant Hybrid Search & RAG Pipeline
* **Thư mục liên quan**: `hybrid_search_demo/`
* **Các bước kỹ thuật**:
  1. Cập nhật `config.py`: Đổi `dense_model_name` trỏ tới `fine-tune-nomic/checkpoints/uth-nomic-embed-v2`.
  2. Re-index toàn bộ dữ liệu 41 môn học UTH vào Qdrant Vector DB với mô hình mới.
  3. Chạy thử nghiệm các câu hỏi truy vấn thực tế của sinh viên UTH và kiểm tra kết quả RRF Re-ranking.
