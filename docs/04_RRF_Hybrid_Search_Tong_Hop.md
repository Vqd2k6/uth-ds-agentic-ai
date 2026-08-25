# Tổng quan về Hybrid Search & Thuật toán Reciprocal Rank Fusion (RRF)

**Hybrid Search (Tìm kiếm hỗn hợp)** kết hợp giữa **Dense Retrieval** (Biểu diễn ngữ nghĩa bằng Deep Learning) và **Sparse Retrieval** (Khớp từ khóa bằng BM25). **Reciprocal Rank Fusion (RRF)** là thuật toán tái xếp hạng (Re-ranking) chuẩn mực để dung hợp các danh sách kết quả từ hai kênh này thành một danh sách tối ưu duy nhất.

---

## 1. Vấn đề Lệch Thang điểm (Score Discrepancy Problem)

Khi kết hợp hai mô hình tìm kiếm khác nhau, điểm số tuyệt đối của chúng không thể so sánh trực tiếp:

| Kênh Tìm kiếm | Thang điểm | Ví dụ Điểm số | Đặc điểm |
| :--- | :--- | :--- | :--- |
| **Dense Search (Cosine)** | $[0.0, 1.0]$ | $0.9995, 0.4185$ | Điểm đồng đều, nằm trong phạm vi cố định |
| **Sparse Search (BM25)** | $[0.0, +\infty)$ | $1.1978, 0.9355$ | Điểm biến động mạnh theo số lần xuất hiện từ |

> [!CAUTION]
> Nếu cộng điểm trực tiếp $\text{Score}_{\text{Total}} = \text{Score}_{\text{Dense}} + \text{Score}_{\text{BM25}}$, điểm số BM25 có nguy cơ áp đảo điểm Cosine. Việc chuẩn hóa Min-Max Score cũng dễ bị sai lệch do sự xuất hiện của các giá trị ngoại lệ (Outliers).

---

## 2. Công thức Toán học Thuật toán RRF

RRF giải quyết vấn đề bằng cách **loại bỏ hoàn toàn điểm số tuyệt đối**, chỉ dựa trên **THỨ HẠNG (Rank $r$)** của văn bản trong từng danh sách kết quả:

$$RRF\_Score(d \in D) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

* **$M$**: Tập các công cụ tìm kiếm ($M = \{\text{Dense}, \text{Sparse}\}$).
* **$r_m(d)$**: Thứ hạng của tài liệu $d$ trong công cụ $m$ (vị trí $1, 2, 3, \dots$).
* **$k = 60$**: Hằng số mịn (Smoothing Constant) tiêu chuẩn nghiên cứu.
  * Hằng số $k$ ngăn việc tài liệu đứng thứ nhất ($r=1$) nhận trọng số quá vượt trội so với tài liệu đứng thứ hai ($r=2$).

---

## 3. Ví dụ Thực tế Tính toán Dung hợp RRF từ Bộ dữ liệu UTH

Tiếp tục sử dụng **$N = 3$ tài liệu mẫu UTH** từ ví dụ của `BM25_Tong_Hop.md` và `Nomic_MoE_v2_Tong_Hop.md`:
* **$d_1$**: `"Sinh viên UTH cần hoàn thành tối thiểu 130 tín chỉ để ra trường."`
* **$d_2$**: `"Môn học Đại số Tuyến tính giảng dạy về không gian vector..."`
* **$d_3$**: `"Nhà trường thông báo lịch nghỉ lễ Tết Nguyên Đán cho toàn thể sinh viên."`

---

### BƯỚC 1: Lấy Danh sách Thứ hạng từ 2 Kênh Tìm kiếm

Giả sử kết quả tìm kiếm độc lập từ 2 luồng như sau:

1. **Luồng Dense Search (Nomic MoE v2)**:
   * Rank 1: $d_1$ (Cosine: $0.9995$) $\Rightarrow r_{\text{Dense}}(d_1) = 1$
   * Rank 2: $d_3$ (Cosine: $0.4185$) $\Rightarrow r_{\text{Dense}}(d_3) = 2$
   * Rank 3: $d_2$ (Cosine: $0.2483$) $\Rightarrow r_{\text{Dense}}(d_2) = 3$

2. **Luồng Sparse Search (BM25)**:
   * Rank 1: $d_1$ (BM25: $1.1978$) $\Rightarrow r_{\text{BM25}}(d_1) = 1$
   * Rank 2: $d_2$ (BM25: $0.9355$) $\Rightarrow r_{\text{BM25}}(d_2) = 2$
   * Rank 3: $d_3$ (BM25: $0.0000$) $\Rightarrow r_{\text{BM25}}(d_3) = 3$

---

### BƯỚC 2: Tính điểm RRF cho từng Tài liệu ($k=60$)

Áp dụng công thức $RRF(d) = \frac{1}{60 + r_{\text{Dense}}(d)} + \frac{1}{60 + r_{\text{BM25}}(d)}$:

* **Tính cho $d_1$**:
  $$RRF(d_1) = \frac{1}{60 + 1} + \frac{1}{60 + 1} = \frac{1}{61} + \frac{1}{61} \approx 0.016393 + 0.016393 = \mathbf{0.032786}$$

* **Tính cho $d_2$**:
  $$RRF(d_2) = \frac{1}{60 + 3} + \frac{1}{60 + 2} = \frac{1}{63} + \frac{1}{62} \approx 0.015873 + 0.016129 = \mathbf{0.032002}$$

* **Tính cho $d_3$**:
  $$RRF(d_3) = \frac{1}{60 + 2} + \frac{1}{60 + 3} = \frac{1}{62} + \frac{1}{63} \approx 0.016129 + 0.015873 = \mathbf{0.032002}$$

---

### BƯỚC 3: Kết quả Đẩy ra (Final Hybrid Ranked Output)

| Thứ hạng (Rank) | ID | Nội dung Tài liệu | Điểm RRF Final | Đánh giá Sức mạnh Dung hợp |
| :---: | :---: | :--- | :---: | :--- |
| **Top 1** | $d_1$ | `"Sinh viên UTH cần hoàn thành tối thiểu 130 tín chỉ..."` | **0.032786** | **Chiến thắng tuyệt đối** vì xuất hiện ở Top 1 trên CẢ HAI kênh! |
| **Top 2** | $d_2$ | `"Môn học Đại số Tuyến tính..."` | **0.032002** | Được BM25 kéo thứ hạng nhờ trùng khớp từ vựng. |
| **Top 3** | $d_3$ | `"Nhà trường thông báo lịch nghỉ lễ..."` | **0.032002** | Được Nomic MoE kéo thứ hạng nhờ có ngữ cảnh nhà trường. |

---

## 4. Ứng dụng trong Hệ thống Agentic AI (RAG Architecture)

Trong kiến trúc **Agentic AI**, Hybrid Search RRF đóng vai trò là một **Retriever Tool (Công cụ tra cứu)** siêu chính xác giúp LLM trả lời dựa trên tri thức thực tế:

```
┌─────────────────┐      1. User Query      ┌─────────────────────────┐
│     USER        ├────────────────────────►│  AGENTIC AI (LLM CORE)  │
└─────────────────┘                         └────────────┬────────────┘
                                                         │
                                    2. Invoke Tool       │
                                    qdrant_hybrid_search │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │ QDRANT HYBRID RETRIEVER │
                                            │ (Nomic MoE + BM25 + RRF)│
                                            └────────────┬────────────┘
                                                         │
                                    3. Grounded Context  │
                                    (Top-K Passages)     │
                                                         ▼
┌─────────────────┐     4. Final Answer     ┌─────────────────────────┐
│   USER SCREEN   │◄────────────────────────┤  LLM GENERATION PHASE   │
└─────────────────┘                         └─────────────────────────┘
```
