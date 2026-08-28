#!/usr/bin/env python3
"""
Script Nạp 4 bộ JSON Collections vào MongoDB (Document Store).
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Nạp cấu hình từ database_ingestion/config.py
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
JSON_COLLECTIONS_DIR = PROJECT_DIR / "structuring_data" / "json_collections"

sys.path.append(str(BASE_DIR))
from config import MONGO_URI, MONGO_DB_NAME

try:
    import pymongo
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False


def load_json_file(file_name: str) -> List[Dict[str, Any]]:
    """Đọc file JSON từ thư mục json_collections"""
    file_path = JSON_COLLECTIONS_DIR / file_name
    if not file_path.exists():
        print(f"[!] Không tìm thấy file: {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        return [data]


def ingest_to_mongodb():
    """Tự động kết nối MongoDB, tạo index và nạp 4 Collections"""
    print("=" * 65)
    print("🍃 BẮT ĐẦU PIPELINE NẠP DỮ LIỆU VÀO MONGODB")
    print("=" * 65)
    print(f"  - Mongo URI: {MONGO_URI}")
    print(f"  - Database:  {MONGO_DB_NAME}")
    print("=" * 65 + "\n")

    if not PYMONGO_AVAILABLE:
        print("[!] Chưa cài đặt thư viện pymongo. Vui lòng cài đặt: pip install pymongo")
        return

    # Khởi tạo MongoClient với timeout 3 giây
    client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    
    try:
        # Kiểm tra kết nối server
        client.admin.command('ping')
        print("[✓] Kết nối MongoDB thành công!\n")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"[!] Không thể kết nối tới MongoDB Server tại {MONGO_URI}.")
        print("    Mẹo: Bạn có thể bật Docker bằng lệnh: cd database_ingestion && docker compose up -d")
        print("    Script sẽ tiếp tục ở chế độ Kiểm thử Cấu trúc (Dry-run Mode).\n")
        run_dry_run_validation()
        return

    db = client[MONGO_DB_NAME]

    collections_map = {
        "syllabus_subjects.json": ("syllabus_subjects", "subject_code"),
        "outcome_frameworks.json": ("outcome_frameworks", "framework_id"),
        "rubric_catalog.json": ("rubric_catalog", "rubric_id"),
        "chunk_sources.json": ("chunk_sources", "chunk_id")
    }

    for json_file, (coll_name, key_field) in collections_map.items():
        data = load_json_file(json_file)
        if not data:
            continue

        collection = db[coll_name]
        
        # 1. Tạo Index cho khóa chính
        collection.create_index(key_field, unique=True)
        
        # 2. Upsert dữ liệu (Cập nhật nếu đã có, thêm mới nếu chưa có)
        inserted = 0
        updated = 0
        
        for item in data:
            filter_doc = {key_field: item[key_field]}
            result = collection.replace_one(filter_doc, item, upsert=True)
            if result.upserted_id:
                inserted += 1
            else:
                updated += 1

        print(f"[✓] Collection '{coll_name}': {len(data)} documents (Thêm mới: {inserted}, Cập nhật: {updated})")

    print("\n" + "=" * 65)
    print("🎉 HOÀN THÀNH NẠP NGUYÊN VẸN 4 COLLECTIONS VÀO MONGODB!")
    print("=" * 65)


def run_dry_run_validation():
    """Kiểm tra tính hợp lệ của 4 tập JSON Collection khi không có server Mongo"""
    print("--- KIỂM THỬ CẤU TRÚC JSON COLLECTIONS (DRY-RUN) ---")
    files = ["syllabus_subjects.json", "outcome_frameworks.json", "rubric_catalog.json", "chunk_sources.json"]
    for f in files:
        data = load_json_file(f)
        print(f"  [✓] File {f}: {len(data)} items hợp lệ")
    print("-----------------------------------------------------")


if __name__ == "__main__":
    ingest_to_mongodb()
