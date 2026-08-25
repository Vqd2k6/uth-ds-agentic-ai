# Tổng quan về Thuật toán Okapi BM25 & TF-IDF

**Okapi BM25** (Best Match 25) là thuật toán xếp hạng văn bản theo độ liên quan (relevance) dựa trên mô hình xác suất (Probabilistic Information Retrieval), được phát triển từ những năm 1970–1980 và là tiêu chuẩn mặc định trong các công cụ tìm kiếm hiện đại như **Elasticsearch**, **Lucene**, **Qdrant Sparse Search**.

---

## 1. Input, Output và Cơ chế hoạt động Cốt lõi

### A. Input (Đầu vào)
* **Tập văn bản (Corpus $D$)**: Danh sách $N$ văn bản $d_1, d_2, ..., d_N$.
* **Truy vấn (Query $q$)**: Dãy các từ khóa tìm kiếm $\{t_1, t_2, ..., t_m\}$.
* **Tham số cấu hình mặc định**:
  * $k_1 = 1.2$: Kiểm soát mức bão hòa tần suất xuất hiện từ.
  * $b = 0.75$: Kiểm soát mức phạt theo độ dài văn bản.

### B. Output (Đầu ra)
* **BM25 Score**: Điểm số thực $Score(q, d) \in [0, +\infty)$ phản ánh mức độ khớp từ khóa giữa truy vấn $q$ và từng văn bản $d$.
* **Sparse Vector (Vectơ thưa)**: Dạng dữ liệu gồm mảng các ID từ vựng (`indices`) và trọng số BM25 tương ứng (`values`).

---

### C. Ví dụ Thực tế Tính toán Chi tiết từ A đến Z

Giả sử hệ thống lưu trữ **$N = 3$ tài liệu mẫu** ($D = \{d_1, d_2, d_3\}$):
* **$d_1$**: `"tín chỉ UTH"` *(Độ dài $|d_1| = 3$ từ)*
* **$d_2$**: `"tín chỉ môn học tại UTH bao gồm tín chỉ lý thuyết"` *(Độ dài $|d_2| = 10$ từ)*
* **$d_3$**: `"trường đại học giao thông vận tải"` *(Độ dài $|d_3| = 6$ từ)*

**Truy vấn của người dùng ($q$)**: `"tín chỉ UTH"` (Gồm 2 từ khóa: $t_1 = \text{"tín chỉ"}$, $t_2 = \text{"UTH"}$).

---

#### BƯỚC 1: Tiền xử lý & Tính độ dài trung bình ($\text{avgdl}$)
* Độ dài trung bình của toàn tập tài liệu:
  $$\text{avgdl} = \frac{|d_1| + |d_2| + |d_3|}{3} = \frac{3 + 10 + 6}{3} = \frac{19}{3} \approx 6.33 \text{ từ}$$

---

#### BƯỚC 2: Tính chỉ số IDF (Inverse Document Frequency) cho từng từ khóa
* Từ khóa $t_1 = \text{"tín chỉ"}$ xuất hiện trong $d_1$ và $d_2 \Rightarrow \text{docFreq}(\text{"tín chỉ"}) = 2$.
* Từ khóa $t_2 = \text{"UTH"}$ xuất hiện trong $d_1$ và $d_2 \Rightarrow \text{docFreq}(\text{"UTH"}) = 2$.

Áp dụng công thức IDF của BM25:
$$\text{idf}(t) = \ln\left(1 + \frac{N - \text{docFreq}(t) + 0.5}{\text{docFreq}(t) + 0.5}\right)$$

* $\text{idf}(\text{"tín chỉ"}) = \ln\left(1 + \frac{3 - 2 + 0.5}{2 + 0.5}\right) = \ln(1 + 0.6) = \ln(1.6) \approx 0.4700$
* $\text{idf}(\text{"UTH"}) = \ln(1.6) \approx 0.4700$

---

#### BƯỚC 3: Tính BM25 Score cho từng văn bản

Công thức thành phần trọng số tần suất $\text{TF}_{\text{BM25}}$:
$$\text{TF}_{\text{BM25}}(t, d) = \frac{\text{freq}(t, d) \cdot (k_1 + 1)}{\text{freq}(t, d) + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{\text{avgdl}}\right)}$$

Với $k_1 = 1.2, b = 0.75$, ta tính cho từng văn bản:

##### 1. Tính toán trên Văn bản $d_1$ ($|d_1| = 3$):
Hệ số phạt độ dài $K(d_1) = 1.2 \times \left(1 - 0.75 + 0.75 \times \frac{3}{6.33}\right) = 1.2 \times (0.25 + 0.3554) \approx 0.7265$
* $\text{TF}_{\text{BM25}}(\text{"tín chỉ"}, d_1) = \frac{1 \times 2.2}{1 + 0.7265} \approx 1.2743$
* $\text{TF}_{\text{BM25}}(\text{"UTH"}, d_1) = \frac{1 \times 2.2}{1 + 0.7265} \approx 1.2743$
* **$\text{Score}_{\text{BM25}}(q, d_1) = (0.4700 \times 1.2743) + (0.4700 \times 1.2743) \approx 0.5989 + 0.5989 = 1.1978$**

##### 2. Tính toán trên Văn bản $d_2$ ($|d_2| = 10$):
Hệ số phạt độ dài $K(d_2) = 1.2 \times \left(1 - 0.75 + 0.75 \times \frac{10}{6.33}\right) = 1.2 \times (0.25 + 1.1848) \approx 1.7218$
* Từ "tín chỉ" xuất hiện 2 lần trong $d_2 \Rightarrow \text{freq} = 2$:
  $$\text{TF}_{\text{BM25}}(\text{"tín chỉ"}, d_2) = \frac{2 \times 2.2}{2 + 1.7218} = \frac{4.4}{3.7218} \approx 1.1822$$
* Từ "UTH" xuất hiện 1 lần trong $d_2 \Rightarrow \text{freq} = 1$:
  $$\text{TF}_{\text{BM25}}(\text{"UTH"}, d_2) = \frac{1 \times 2.2}{1 + 1.7218} = \frac{2.2}{2.7218} \approx 0.8083$$
* **$\text{Score}_{\text{BM25}}(q, d_2) = (0.4700 \times 1.1822) + (0.4700 \times 0.8083) \approx 0.5556 + 0.3799 = 0.9355$**

##### 3. Tính toán trên Văn bản $d_3$ ($|d_3| = 6$):
Không chứa từ nào trong truy vấn $\Rightarrow \mathbf{\text{Score}_{\text{BM25}}(q, d_3) = 0.0000}$

---

#### BƯỚC 4: Kết quả Đẩy ra (Output Final Ranking)

| Thứ hạng (Rank) | ID Văn bản | Nội dung | Điểm BM25 Score | Lý do Giành chiến thắng |
| :---: | :---: | :--- | :---: | :--- |
| **Top 1** | $d_1$ | `"tín chỉ UTH"` | **1.1978** | Ngắn gọn, súc tích (3 từ) $\rightarrow$ Không bị phạt độ dài |
| **Top 2** | $d_2$ | `"tín chỉ môn học tại UTH..."` | **0.9355** | Dài (10 từ) nên bị phạt độ dài dù chứa 2 lần từ "tín chỉ" |
| **Top 3** | $d_3$ | `"trường đại học..."` | **0.0000** | Không trùng từ khóa nào |

> [!NOTE]
> **Bài học quan trọng từ ví dụ**: $d_1$ ngắn gọn (3 từ) nên đạt điểm cao hơn $d_2$ (10 từ), cho dù $d_2$ xuất hiện từ "tín chỉ" tới 2 lần. Đây chính là minh chứng rõ ràng nhất cho tính năng **Chuẩn hóa độ dài văn bản (Length Normalization)** của BM25!

---

## 2. Nền tảng: Mô hình TF-IDF

BM25 là bản cải tiến vượt trội dựa trên nền tảng của **TF-IDF** (Term Frequency - Inverse Document Frequency). Dưới đây là 3 yếu tố cốt lõi của TF-IDF:

* **TF (Term Frequency):** Tần suất xuất hiện của từ ($t$) trong văn bản ($d$).
  $$\text{tf}(t, d) = \sqrt{\text{frequency}}$$
  * *Ý nghĩa:* Tần suất xuất hiện càng nhiều thì độ liên quan càng cao, nhưng tăng theo căn bậc hai thay vì tuyến tính.
* **IDF (Inverse Document Frequency):** Độ đặc biệt/hiếm của từ trên toàn bộ tập văn bản.
  $$\text{idf}(t) = \ln\left(\frac{\text{numDocs}}{\text{docFreq} + 1}\right) + 1$$
  * *Ý nghĩa:* Từ càng hiếm xuất hiện trong các tài liệu khác thì giá trị thông tin mang lại càng cao.
* **Document Length Norm (Norm):** Chuẩn hóa độ dài trường/văn bản.
  $$\text{norm}(d) = \frac{1}{\sqrt{\text{numTerms}}}$$

$$\text{Score}_{\text{TF-IDF}} = \text{IDF} \times \text{TF} \times \text{Norm}$$

---

## 3. Cải tiến cốt lõi của BM25

BM25 giải quyết hai hạn chế chính của TF-IDF:

1. **Điểm bão hòa tần suất (TF Saturation):** Trong TF-IDF, TF tăng vô hạn khi số lần xuất hiện tăng. Trong BM25, TF tiệm cận tới một ngưỡng cực đại (bão hòa) để tránh việc lặp từ cố tình (Keyword Stuffing) bóp méo kết quả.
2. **Độ dài tài liệu linh hoạt (Document Length Normalization):** Tự điều chỉnh trọng số linh hoạt theo tỉ lệ độ dài tài liệu hiện tại so với độ dài trung bình toàn tập ($\text{avgdl}$).

---

## 4. Công thức BM25 Chi tiết

### a. IDF trong BM25
Tính toán lại để phạt (cho điểm âm) nếu từ xuất hiện ở quá nhiều tài liệu ($>\frac{N}{2}$):

$$\text{idf}(t) = \ln\left(1 + \frac{\text{docCount} - \text{docFreq} + 0.5}{\text{docFreq} + 0.5}\right)$$

### b. TF & Chuẩn hóa độ dài trong BM25

$$\text{TF}_{\text{BM25}} = \frac{\text{freq} \cdot (k_1 + 1)}{\text{freq} + k_1 \cdot \left(1 - b + b \cdot \frac{\text{fieldLength}}{\text{avgFieldLength}}\right)}$$

* **$k_1 = 1.2$:** Giới hạn tốc độ bão hòa TF.
* **$b = 0.75$:** Mức độ ảnh hưởng của độ dài văn bản.
* **$\frac{\text{fieldLength}}{\text{avgFieldLength}}$:** Tỉ lệ độ dài văn bản hiện tại so với trung bình toàn tập.

### c. Công thức BM25 Tổng quát

$$\text{Score}_{\text{BM25}}(q, d) = \sum_{t \in q} \text{idf}(t) \cdot \frac{\text{freq}(t, d) \cdot (k_1 + 1)}{\text{freq}(t, d) + k_1 \cdot \left(1 - b + b \cdot \frac{|d|}{\text{avgdl}}\right)}$$

---

## 5. Bảng So sánh Tổng hợp

| Tiêu chí | TF-IDF | BM25 |
| :--- | :--- | :--- |
| **Mô hình** | Thống kê tần suất đơn thuần | Mô hình xác suất (Probabilistic IR) |
| **Tăng trưởng TF** | Tăng theo căn bậc hai (không giới hạn) | Tiệm cận điểm bão hòa (giới hạn bởi $k_1$) |
| **Chuẩn hóa độ dài** | Chia cho căn bậc hai tổng số từ | So sánh với độ dài trung bình ($\text{avgdl}$) qua tham số $b$ |
| **Ưu điểm** | Đơn giản, tính nhanh | Rất chính xác với truy vấn chứa từ khóa, tên riêng, mã số |
| **Nhược điểm** | Mù ngữ nghĩa, dễ bỏ sót từ đồng nghĩa | Mù ngữ nghĩa, phụ thuộc hoàn toàn vào trùng khớp từ vựng |
