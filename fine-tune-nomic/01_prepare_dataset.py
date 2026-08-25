"""
Phase 1: Dataset Preparation Script
Trích xuất chunks từ 41 thư mục đề cương học phần UTH trong output/ 
và khởi tạo bộ dữ liệu cặp (Query, Positive Doc) cho Fine-tuning Nomic MoE v2.
"""
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PrepareDataset")

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output"
DATASET_DIR = Path(__file__).parent / "dataset"
DATASET_DIR.mkdir(parents=True, exist_ok=True)

PREFIX_QUERY = "search_query: "
PREFIX_DOC = "search_document: "


def load_markdown_files() -> List[Dict[str, str]]:
    """Duyệt qua 41 thư mục học phần trong output/ để đọc nội dung các file .md."""
    documents: List[Dict[str, str]] = []
    
    if not OUTPUT_DIR.exists():
        logger.error(f"Thư mục output không tồn tại tại: {OUTPUT_DIR}")
        return documents

    for course_folder in OUTPUT_DIR.iterdir():
        if course_folder.is_dir():
            # Tìm thư mục con hybrid_auto nếu có
            target_folder = course_folder / "hybrid_auto"
            search_dir = target_folder if target_folder.exists() else course_folder
            
            for md_file in search_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8").strip()
                    if content:
                        documents.append({
                            "folder_name": course_folder.name,
                            "file_name": md_file.name,
                            "content": content
                        })
                except Exception as err:
                    logger.warning(f"Không thể đọc file {md_file}: {err}")

    logger.info(f"Đã đọc tổng cộng {len(documents)} file Markdown đề cương học phần.")
    return documents


def chunk_document(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """Cắt nhỏ văn bản thành các chunks có độ dài từ 300-500 từ."""
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        start += (chunk_size - overlap)
    return chunks


def generate_synthetic_queries(chunk: str, folder_name: str) -> List[str]:
    """Tạo ra các câu hỏi mô phỏng sinh viên UTH dựa trên từ khóa và tiêu đề học phần."""
    queries = []
    
    # Tách mã học phần và tên môn học từ folder_name (VD: "124100 - Ngon ngu lap trinh Python - DCCT")
    parts = folder_name.split(" - ")
    code = parts[0].strip() if len(parts) > 0 else ""
    name = parts[1].strip() if len(parts) > 1 else folder_name

    # Mẫu câu hỏi sinh viên thường gặp
    if code and name:
        queries.append(f"Mã học phần {code} ({name}) giảng dạy những nội dung gì?")
        queries.append(f"Quy định số tín chỉ và thông tin môn học {name} ({code}) tại UTH?")
        queries.append(f"Chuẩn đầu ra CĐR và mục tiêu của học phần {name} là gì?")
    elif name:
        queries.append(f"Thông tin chi tiết về môn học {name} tại Trường UTH?")
        queries.append(f"Đề cương chi tiết học phần {name} quy định thế nào?")

    # Rút trích các dòng tiêu đề trong chunk để làm câu hỏi cụ thể
    lines = chunk.split("\n")
    for line in lines:
        line_clean = line.strip("#-* ").strip()
        if len(line_clean) > 10 and len(line_clean) < 80 and not line_clean.startswith("http"):
            queries.append(f"Quy định về {line_clean} trong học phần {name}?")
            break

    return queries


def build_dataset():
    logger.info("=== BẮT ĐẦU CHUẨN BỊ DATASET CHO FINE-TUNING NOMIC MOE V2 ===")
    
    docs = load_markdown_files()
    if not docs:
        logger.error("Không tìm thấy dữ liệu đề cương trong output/. Dừng chương trình.")
        return

    all_pairs: List[Dict[str, str]] = []
    total_chunks = 0

    for item in docs:
        chunks = chunk_document(item["content"])
        total_chunks += len(chunks)
        
        for chunk in chunks:
            queries = generate_synthetic_queries(chunk, item["folder_name"])
            for q in queries:
                all_pairs.append({
                    "query": f"{PREFIX_QUERY}{q}",
                    "positive_doc": f"{PREFIX_DOC}{chunk}"
                })

    logger.info(f"Tổng số Chunks được tạo ra: {total_chunks}")
    logger.info(f"Tổng số Cặp (Query, Positive Doc) được tạo ra: {len(all_pairs)}")

    # Xáo trộn và chia Train/Test Split (80% Train, 20% Test)
    random.seed(42)
    random.shuffle(all_pairs)
    
    split_idx = int(len(all_pairs) * 0.8)
    train_pairs = all_pairs[:split_idx]
    test_pairs = all_pairs[split_idx:]

    train_path = DATASET_DIR / "train_pairs.json"
    test_path = DATASET_DIR / "test_pairs.json"

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_pairs, f, ensure_ascii=False, indent=2)

    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_pairs, f, ensure_ascii=False, indent=2)

    logger.info(f"Đã lưu {len(train_pairs)} mẫu train tại: {train_path}")
    logger.info(f"Đã lưu {len(test_pairs)} mẫu test tại: {test_path}")
    logger.info("=== HOÀN THÀNH PHASE 1: CHUẨN BỊ DATASET ===")


if __name__ == "__main__":
    build_dataset()
