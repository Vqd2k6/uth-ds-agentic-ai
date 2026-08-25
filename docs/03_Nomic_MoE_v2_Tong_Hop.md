# Tổng quan về Mô hình Nomic Embed Text MoE v2 & Dense Embeddings

**Nomic Embed Text MoE v2** (`nomic-ai/nomic-embed-text-v2-moe`) là mô hình tạo vectơ nhúng ngữ nghĩa (Text Embedding) mã nguồn mở đầu tiên áp dụng kiến trúc **Mixture-of-Experts (MoE)**, hỗ trợ đa ngôn ngữ và tối ưu hóa chuyên sâu cho các ứng dụng **Retrieval-Augmented Generation (RAG)** và **Agentic AI**.

---

## 1. Sơ đồ Quy trình Dense Embedding Hoàn chỉnh (Offline & Real-time)

Quy trình xử lý dữ liệu với Nomic MoE v2 được chia thành 2 giai đoạn độc lập:

```
===========================================================================
GIAI ĐOẠN 1: OFFLINE INDEXING (Chạy 1 lần ban đầu để chuẩn bị kho dữ liệu)
===========================================================================
[Tài liệu văn bản] ──► Gắn prefix "search_document: " ──► [Nomic MoE v2]
                                                               │
                                                               ▼
[Qdrant Vector DB] ◄── LƯU TRỮ CÁC DENSE VECTORS ◄── [768-D Document Vectors]

===========================================================================
GIAI ĐOẠN 2: REAL-TIME QUERYING (Chạy mỗi khi người dùng đặt câu hỏi)
===========================================================================
[Câu hỏi người dùng] ──► Gắn prefix "search_query: " ──► [Nomic MoE v2]
                                                               │
                                                               ▼
                                                  [768-D Query Vector]
                                                               │
                                                               ▼
                                                  [So sánh Cosine Similarity]
                                                               │
                                                               ▼
[BẢNG KẾT QUẢ TOP DOCS] ◄──────────────────────────────────────┘
```

---

## 2. Input, Output và Quy tắc Prefix Bắt buộc

### A. Input (Đầu vào)
* **Dữ liệu**: Chuỗi văn bản thuần (Text string).
* **Quy tắc Prefix (Tiền tố bắt buộc)**:
  * Khi mã hóa tài liệu lưu trữ vào cơ sở dữ liệu: Thêm prefix `search_document: `
    * *Ví dụ:* `"search_document: Quy chế đào tạo UTH quy định 130 tín chỉ."`
  * Khi mã hóa câu truy vấn của người dùng: Thêm prefix `search_query: `
    * *Ví dụ:* `"search_query: Sinh viên UTH học bao nhiêu tín chỉ?"`

### B. Output (Đầu ra)
* **Dense Vector (Vectơ dày/đặc)**: Một mảng cố định **768 số thực liên tục** (Float32).
  $$\mathbf{v} = [v_1, v_2, v_3, \dots, v_{768}] \in \mathbb{R}^{768}$$
* **Ý nghĩa toán học**: Vectơ nén toàn bộ thông tin ngữ nghĩa (ý tưởng, mối quan hệ chủ đề, ngữ cảnh) của văn bản vào một tọa độ trong không gian 768 chiều.

---

### C. Ví dụ Thực tế Tính toán & Mã hóa Chi tiết từ A đến Z

Giả sử hệ thống cần mã hóa **$N = 3$ tài liệu mẫu** vào cơ sở dữ liệu:
* **$d_1$**: `"Sinh viên UTH cần hoàn thành tối thiểu 130 tín chỉ để ra trường."`
* **$d_2$**: `"Môn học Đại số Tuyến tính giảng dạy về không gian vector và ma trận."`
* **$d_3$**: `"Nhà trường thông báo lịch nghỉ lễ Tết Nguyên Đán cho toàn thể sinh viên."`

**Truy vấn của người dùng ($q$)**: `"Quy định số lượng tín chỉ tốt nghiệp của trường UTH"`

---

#### BƯỚC 1: Chuẩn hóa Prefix & Mã hóa qua Nomic MoE v2

1. **Gắn tiền tố đúng quy chuẩn**:
   * $d_1'$: `"search_document: Sinh viên UTH cần hoàn thành tối thiểu 130 tín chỉ để ra trường."`
   * $d_2'$: `"search_document: Môn học Đại số Tuyến tính giảng dạy về không gian vector và ma trận."`
   * $d_3'$: `"search_document: Nhà trường thông báo lịch nghỉ lễ Tết Nguyên Đán cho toàn thể sinh viên."`
   * $q'$: `"search_query: Quy định số lượng tín chỉ tốt nghiệp của trường UTH"`

2. **Mô hình MoE định tuyến & sinh ra Dense Vectors (768 chiều)**:
   *(Dưới đây trích xuất minh họa 4 chiều tiêu biểu trong 768 chiều để dễ theo dõi tính toán)*:
   * $\mathbf{v}_{d1} = [0.85, 0.12, 0.91, 0.05]$ *(Tọa độ thiên về chủ đề: Quy chế / Tín chỉ UTH)*
   * $\mathbf{v}_{d2} = [0.08, 0.94, 0.15, 0.02]$ *(Tọa độ thiên về chủ đề: Toán học / Đại số)*
   * $\mathbf{v}_{d3} = [0.42, 0.05, 0.10, 0.88]$ *(Tọa độ thiên về chủ đề: Thông báo / Nghỉ lễ)*
   * $\mathbf{v}_{q}  = [0.88, 0.10, 0.94, 0.08]$ *(Tọa độ câu hỏi: Yêu cầu tín chỉ tốt nghiệp UTH)*

---

#### BƯỚC 2: Tính toán Độ tương đồng Cosine Similarity

Công thức Cosine Similarity giữa Vector câu hỏi $\mathbf{v}_q$ và từng Vector tài liệu $\mathbf{v}_d$:

$$\text{Cosine}(\mathbf{v}_q, \mathbf{v}_d) = \frac{\mathbf{v}_q \cdot \mathbf{v}_d}{\|\mathbf{v}_q\| \|\mathbf{v}_d\|} = \frac{\sum_{i=1}^{768} (v_{q, i} \times v_{d, i})}{\sqrt{\sum_{i=1}^{768} v_{q, i}^2} \times \sqrt{\sum_{i=1}^{768} v_{d, i}^2}}$$

1. **Tính Cosine giữa $q$ và $d_1$**:
   * Tích vô hướng: $\mathbf{v}_q \cdot \mathbf{v}_{d1} = (0.88 \times 0.85) + (0.10 \times 0.12) + (0.94 \times 0.91) + (0.08 \times 0.05) = 0.7480 + 0.0120 + 0.8554 + 0.0040 = 1.6194$
   * Độ dài $\|\mathbf{v}_q\| = \sqrt{0.88^2 + 0.10^2 + 0.94^2 + 0.08^2} = \sqrt{0.7744 + 0.0100 + 0.8836 + 0.0064} = \sqrt{1.6744} \approx 1.2940$
   * Độ dài $\|\mathbf{v}_{d1}\| = \sqrt{0.85^2 + 0.12^2 + 0.91^2 + 0.05^2} = \sqrt{0.7225 + 0.0144 + 0.8281 + 0.0025} = \sqrt{1.5675} \approx 1.2520$
   * **$\text{Cosine}(\mathbf{v}_q, \mathbf{v}_{d1}) = \frac{1.6194}{1.2940 \times 1.2520} = \frac{1.6194}{1.6201} \approx \mathbf{0.9995}$** *(Tương đồng ngữ nghĩa tuyệt đối!)*

2. **Tính Cosine giữa $q$ và $d_2$ (Toán học)**:
   * $\mathbf{v}_q \cdot \mathbf{v}_{d2} = (0.88 \times 0.08) + (0.10 \times 0.94) + (0.94 \times 0.15) + (0.08 \times 0.02) = 0.0704 + 0.0940 + 0.1410 + 0.0016 = 0.3070$
   * Độ dài $\|\mathbf{v}_{d2}\| = \sqrt{0.08^2 + 0.94^2 + 0.15^2 + 0.02^2} = \sqrt{0.0064 + 0.8836 + 0.0225 + 0.0004} = \sqrt{0.9129} \approx 0.9555$
   * **$\text{Cosine}(\mathbf{v}_q, \mathbf{v}_{d2}) = \frac{0.3070}{1.2940 \times 0.9555} \approx \mathbf{0.2483}$** *(Khác chủ đề)*

3. **Tính Cosine giữa $q$ và $d_3$ (Lịch nghỉ lễ)**:
   * $\mathbf{v}_q \cdot \mathbf{v}_{d3} = (0.88 \times 0.42) + (0.10 \times 0.05) + (0.94 \times 0.10) + (0.08 \times 0.88) = 0.3696 + 0.0050 + 0.0940 + 0.0704 = 0.5390$
   * **$\text{Cosine}(\mathbf{v}_q, \mathbf{v}_{d3}) \approx \mathbf{0.4185}$** *(Có chứa từ "sinh viên/trường" nhưng khác ý định hỏi)*

---

#### BƯỚC 3: Kết quả Đẩy ra (Output Final Ranking)

| Thứ hạng (Rank) | ID | Nội dung Tài liệu gốc | Cosine Score | Sức mạnh Ngữ nghĩa của Dense Vector |
| :---: | :---: | :--- | :---: | :--- |
| **Top 1** | $d_1$ | `"Sinh viên UTH cần hoàn thành tối thiểu 130 tín chỉ để ra trường."` | **0.9995** | Hiểu được từ *"quy định tín chỉ tốt nghiệp"* tương đương *"tối thiểu 130 tín chỉ để ra trường"* dù câu từ dùng hoàn toàn khác nhau! |
| **Top 2** | $d_3$ | `"Nhà trường thông báo lịch nghỉ lễ..."` | **0.4185** | Nhận diện có liên quan đến môi trường nhà trường nhưng khác ý định chính. |
| **Top 3** | $d_2$ | `"Môn học Đại số Tuyến tính..."` | **0.2483** | Hoàn toàn không liên quan đến quy định tốt nghiệp. |

> [!NOTE]
> **Bài học quan trọng từ ví dụ**: Câu hỏi dùng từ *"tốt nghiệp"*, trong khi văn bản $d_1$ dùng từ *"ra trường"*. BM25 sẽ bỏ sót hoặc chấm điểm rất thấp vì từ không trùng khớp. Nhưng **Nomic MoE v2** hiểu 2 từ này đồng nghĩa trong ngữ cảnh đại học $\rightarrow$ Đạt điểm Cosine tiệm cận $1.0$!

---

## 3. Cơ chế Hoạt động Cốt lõi của Mixture-of-Experts (MoE)

Mô hình Transformer truyền thống phải kích hoạt 100% các tham số cho mọi từ nhập vào. Kiến trúc **MoE (Hỗn hợp các chuyên gia)** giải quyết vấn đề này bằng cơ chế phân chia nhiệm vụ:

```
                          ┌───────────────────────────┐
                          │   INPUT: Prefixed Text    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │ GATING NETWORK / ROUTER   │
                          │ (Định tuyến 2/8 Experts) │
                          └──────┬─────────────┬──────┘
                                 │             │
                    ┌────────────┘             └────────────┐
                    ▼                                       ▼
        ┌───────────────────────┐               ┌───────────────────────┐
        │  Expert 2 (Ngữ pháp)  │               │  Expert 5 (Ngữ nghĩa) │
        └───────────┬───────────┘               └───────────┬───────────┘
                    │                                       │
                    └───────────────────┬───────────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  OUTPUT: 768-D Embedding  │
                          └───────────────────────────┘
```

### Các thông số kỹ thuật chính:
* **Tổng số tham số (Total Parameters)**: 475 triệu tham số (8 Chuyên gia - Experts).
* **Số tham số kích hoạt (Active Parameters)**: Chỉ 305 triệu tham số cho mỗi lượt suy luận (Inference).
* **Thuật toán Router (Top-2 Routing)**: Với mỗi token nhập vào, Gating Network tính toán và chọn đúng **2 Chuyên gia (Experts)** xuất sắc nhất để xử lý.
* **Lợi ích**: Giữ được tri thức khổng lồ của một mô hình đại lớn nhưng chạy nhanh hơn và tốn ít bộ nhớ VRAM hơn $35\%$.

---

## 4. Khoảng cách Cosine & So sánh Không gian Vectơ

Để đo độ tương đồng ngữ nghĩa giữa câu truy vấn ($\mathbf{q}$) và tài liệu ($\mathbf{d}$), người ta dùng phép đo **Cosine Similarity**:

$$\text{Cosine}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\| \|\mathbf{d}\|} = \frac{\sum_{i=1}^{768} q_i \cdot d_i}{\sqrt{\sum_{i=1}^{768} q_i^2} \cdot \sqrt{\sum_{i=1}^{768} d_i^2}}$$

* **Phạm vi giá trị**: $[-1.0, 1.0]$ (Sau khi chuẩn hóa $\mathcal{L}_2$, nằm trong $[0.0, 1.0]$).
* **Bản chất**: Nếu hai đoạn văn có ý nghĩa tương tự (dùng từ đồng nghĩa hoặc câu hỏi - câu trả lời tương ứng), góc $\theta$ giữa hai vectơ sẽ tiệm cận $0^\circ \Rightarrow \cos(\theta) \approx 1.0$.

---

## 5. Tóm tắt So sánh Dense Vector vs Sparse Vector

| Tiêu chí | Dense Vector (Nomic MoE v2) | Sparse Vector (BM25) |
| :--- | :--- | :--- |
| **Bản chất** | Vectơ liên tục, 768 chiều đầy đủ số thực | Vectơ thưa, chiều bằng cỡ từ điển ($|V| > 100k$), đa số bằng 0 |
| **Khả năng bắt ý nghĩa** | Rất mạnh (Nhận diện từ đồng nghĩa, ngữ cảnh sâu) | Không có (Chỉ bắt từ trùng khớp từng ký tự) |
| **Khả năng bắt từ khóa** | Kém hơn với mã số, tên riêng, từ hiếm | Rất mạnh với mã môn học, từ đặc thù |
| **Phép đo khoảng cách** | Cosine Similarity, Dot Product | BM25 Score, TF-IDF Weight |
