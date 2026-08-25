# 📚 Pipeline Tiền Xử Lý Dữ Liệu Đề Cương Học Phần (PDF Preprocessing)

Thư mục này chịu trách nhiệm **chuyển đổi toàn bộ tài liệu Đề cương chi tiết học phần (ĐCCT) và Khung chuẩn đầu ra (PLO - CLO - Rubric) dạng PDF thô** thành dữ liệu tri thức có cấu trúc (**Markdown, JSON, Images**) sử dụng công cụ AI bóc tách tài liệu **MinerU (Magic-PDF)**.

---

## 📂 1. Cấu trúc Thư mục

```plaintext
preprocessing_data/
├── README.md                       # Tài liệu hướng dẫn sử dụng này
├── magic-pdf.json                  # File cấu hình mô hình AI & thiết bị
├── raw_pdfs/                       # Thư mục chứa các file PDF đề cương gốc (41 files)
│   ├── 121000 - Co so du lieu.pdf
│   ├── 121033 - Tri tue nhan tao.pdf
│   ├── 124100 - Ngon ngu lap trinh Python - DCCT.pdf
│   └── ...
├── scripts/
│   └── parse_pdfs.py               # Script tự động hóa bóc tách đơn lẻ hoặc hàng loạt
└── parsed_output/                  # Kết quả bóc tách ra Markdown & JSON
    └── 124100 - Ngon ngu lap trinh Python - DCCT/
        └── txt/
            ├── 124100 - Ngon ngu lap trinh Python - DCCT.md            <-- Nội dung Markdown sạch
            ├── 124100 - Ngon ngu lap trinh Python - DCCT_content_list.json
            ├── 124100 - Ngon ngu lap trinh Python - DCCT_layout.pdf
            └── images/                                                 <-- Hình ảnh bóc tách từ PDF
```

---

## ⚙️ 2. Yêu cầu Môi trường & Thiết lập (Setup)

### 2.1. Cài đặt thư viện Python
Toàn bộ dependencies đã được cài đặt trong môi trường ảo `.venv`:
```bash
# Cài đặt MinerU và các thư viện hỗ trợ (nếu thiết lập mới)
.venv/bin/pip install "magic-pdf[full]"
```

### 2.2. Bộ trọng số mô hình AI (Model Weights)
Mô hình bóc tách tài liệu của MinerU (`opendatalab/PDF-Extract-Kit-1.0`) được lưu tại:
- **Đường dẫn**: `/Users/vqd2k6/magic-pdf-models/models`
- Bao gồm: `Layout` (DocLayout-YOLO), `TabRec` (RapidTable/Slanet-Plus), `OCR`, `MFD`.

### 2.3. Cấu hình file `magic-pdf.json`
File cấu hình được đặt tại `preprocessing_data/magic-pdf.json` và đồng bộ vào `~/magic-pdf.json`:
```json
{
  "models-dir": "/Users/vqd2k6/magic-pdf-models/models",
  "device-mode": "mps",
  "table-config": {
    "model": "rapid_table",
    "enable": true,
    "max_time": 400
  },
  "layout-config": {
    "model": "doclayout_yolo"
  },
  "formula-config": {
    "enable": false
  }
}
```
> **Lưu ý**: `device-mode: "mps"` kích hoạt khả năng tăng tốc GPU Metal trên chip Apple Silicon của máy Mac.

---

## 🚀 3. Hướng dẫn Chạy Pipeline (`parse_pdfs.py`)

### 🔹 Cách 1: Chạy bóc tách toàn bộ 41 môn học (Đa tiến trình song song)
Tự động quét toàn bộ thư mục `raw_pdfs/`, chia tải xử lý song song nhiều file cùng lúc và tự động bỏ qua các file đã hoàn thành:
```bash
.venv/bin/python preprocessing_data/scripts/parse_pdfs.py --all --workers 3
```
*Tùy chỉnh số lượng workers (`-w 3` hoặc `-w 4`) tùy theo số nhân CPU/RAM của máy.*

---

### 🔹 Cách 2: Chạy thử nghiệm trên 1 môn học cụ thể
```bash
# Cú pháp với tên file trong thư mục raw_pdfs
.venv/bin/python preprocessing_data/scripts/parse_pdfs.py --file "124100 - Ngon ngu lap trinh Python - DCCT.pdf"

# Hoặc môn Trí tuệ nhân tạo
.venv/bin/python preprocessing_data/scripts/parse_pdfs.py --file "121033 - Tri tue nhan tao.pdf"
```

---

### 🔹 Cách 3: Chạy thử nghiệm giới hạn số lượng file (Limit)
Chạy thử nghiệm trên $N$ file đầu tiên:
```bash
.venv/bin/python preprocessing_data/scripts/parse_pdfs.py --limit 3 --workers 3
```

---

### 🔹 Cách 4: Bắt buộc parse lại toàn bộ (Force re-parse)
Bỏ qua cache và parse đè lên kết quả cũ:
```bash
.venv/bin/python preprocessing_data/scripts/parse_pdfs.py --all --force --workers 3
```

---

## 📊 4. Cấu trúc Dữ liệu Đầu ra (`parsed_output/`)

Sau khi bóc tách, mỗi môn học sẽ tạo ra các file chuẩn:

| Tên file | Ý nghĩa & Mục đích sử dụng |
| :--- | :--- |
| `*.md` | **Nội dung chính**: Đề cương đã được chuyển thành Markdown (bảng biểu tuần, chuẩn đầu ra, điểm số, học liệu). |
| `*_content_list.json` | Danh sách block văn bản kèm metadata toạ độ, kiểu phần tử (`text`, `table`, `image`). |
| `*_layout.pdf` | File PDF debug trực quan hoá các vùng nhận diện layout. |
| `images/` | Thư mục chứa sơ đồ, ảnh cắt từ tài liệu gốc. |

---

## ⏩ 5. Bước tiếp theo trong Dự án
Sau khi các file Markdown được tạo trong `parsed_output/`:
1. **Trích xuất JSON Schema**: Chuyển đổi Markdown sang các MongoDB Collection theo thiết kế [1-SCHEMA-DESIGNING.md](../1-SCHEMA-DESIGNING.md) (`syllabus_subjects`, `outcome_frameworks`, `rubric_catalog`).
2. **Chunking & Vector DB**: Cắt nhỏ nội dung từng tuần học / mục tiêu và nạp vào Qdrant để phục vụ Hybrid Search (RAG).
3. **Knowledge Graph**: Tạo đồ thị liên kết tri thức giữa các môn học và chuẩn đầu ra trên Neo4j.
