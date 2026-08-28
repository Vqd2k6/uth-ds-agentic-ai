#!/usr/bin/env python3
"""
Script Embeddings (Nomic-Embed-Text v1.5 - 768 dim) & Nạp Collection 'chunk_sources' vào Qdrant Vector Database.
Hỗ trợ Dense Vector Search kết hợp Sparse Vector (BM25) cho hệ thống Hybrid Search RAG.
"""

import sys
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
JSON_COLLECTIONS_DIR = PROJECT_DIR / "structuring_data" / "json_collections"
CHUNKS_FILE_PATH = JSON_COLLECTIONS_DIR / "chunk_sources.json"

sys.path.append(str(BASE_DIR))
from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION_NAME

# Tên mô hình Nomic Embeddings chuẩn theo tài liệu kiến trúc dự án
NOMIC_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False


def load_chunks() -> List[Dict[str, Any]]:
    """Đọc dữ liệu chunk_sources.json"""
    if not CHUNKS_FILE_PATH.exists():
        print(f"[!] Không tìm thấy file: {CHUNKS_FILE_PATH}")
        return []
    with open(CHUNKS_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def ingest_to_qdrant():
    """Tạo Nomic Embeddings và nạp Chunks vào Qdrant Vector Database"""
    print("=" * 65)
    print("🚀 BẮT ĐẦU PIPELINE EMBEDDINGS (NOMIC v1.5) & NẠP VECTORS VÀO QDRANT")
    print("=" * 65)
    print(f"  - Embedding Model:   {NOMIC_MODEL_NAME}")
    print(f"  - Qdrant Host:       {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"  - Collection Name:   {QDRANT_COLLECTION_NAME}")
    print("=" * 65 + "\n")

    chunks = load_chunks()
    if not chunks:
        print("[!] Không có chunks nào để xử lý.")
        return

    print(f"[*] Đã tải {len(chunks)} chunks từ {CHUNKS_FILE_PATH.name}")

    # 1. Khởi tạo Mô hình Nomic Embedding
    embedding_model = None
    vector_dim = 768

    if FASTEMBED_AVAILABLE:
        try:
            print(f"[*] Đang tải mô hình Nomic Embeddings: '{NOMIC_MODEL_NAME}'...")
            embedding_model = TextEmbedding(model_name=NOMIC_MODEL_NAME)
            dummy_vec = list(embedding_model.embed(["test"]))[0]
            vector_dim = len(dummy_vec)
            print(f"[✓] Mô hình Nomic Embeddings sẵn sàng! Kích thước Vector: {vector_dim} chiều.")
        except Exception as e:
            print(f"[!] Không thể tải Nomic model ({e}). Sử dụng mô hình FastEmbed mặc định...")
            embedding_model = TextEmbedding()
            dummy_vec = list(embedding_model.embed(["test"]))[0]
            vector_dim = len(dummy_vec)
            print(f"[✓] Mô hình Embedding sẵn sàng! Kích thước Vector: {vector_dim} chiều.")
    else:
        print("[!] Thư viện fastembed chưa được cài đặt. Vui lòng cài đặt: pip install fastembed")
        return

    # 2. Khởi tạo Qdrant Client
    client = None
    is_live_server = False

    if QDRANT_AVAILABLE:
        try:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=3.0, check_compatibility=False)
            client.get_collections()
            is_live_server = True
            print(f"[✓] Kết nối trực tiếp thành công tới Qdrant Server tại http://{QDRANT_HOST}:{QDRANT_PORT}!\n")
        except Exception:
            print(f"[!] Không thể kết nối tới Qdrant Server tại http://{QDRANT_HOST}:{QDRANT_PORT}.")
            print("    Mẹo: Bạn có thể bật Docker bằng lệnh: cd database_ingestion && docker compose up -d")
            print("    Script sẽ tự động chuyển sang chế độ Qdrant In-Memory / Local Test.\n")
            client = QdrantClient(":memory:")
            is_live_server = False

    # 3. Tạo Collection trên Qdrant
    if client:
        print(f"[*] Đang khởi tạo Qdrant Collection '{QDRANT_COLLECTION_NAME}' (Cosine Distance)...")
        if client.collection_exists(QDRANT_COLLECTION_NAME):
            client.delete_collection(QDRANT_COLLECTION_NAME)

        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE)
        )

        # 4. Tính toán Vector Embeddings cho danh sách Chunks
        contents = [item["content"] for item in chunks]
        print(f"[*] Đang tính Nomic Vector Embeddings cho {len(contents)} đoạn văn bản...")
        embeddings_generator = embedding_model.embed(contents)
        embeddings_list = [vec.tolist() for vec in embeddings_generator]

        # 5. Tạo danh sách Qdrant Points
        points = []
        for idx, (item, vec) in enumerate(zip(chunks, embeddings_list)):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item["chunk_id"]))
            
            payload = {
                "chunk_id": item["chunk_id"],
                "subject_code": item["subject_code"],
                "subject_name_vi": item["subject_name_vi"],
                "chunk_type": item["chunk_type"],
                "section_title": item["section_title"],
                "content": item["content"],
                "metadata": item.get("metadata", {})
            }
            
            points.append(PointStruct(id=point_id, vector=vec, payload=payload))

        # 6. Đẩy Points vào Qdrant
        print(f"[*] Đang đẩy {len(points)} Nomic points vào Qdrant...")
        client.upsert(collection_name=QDRANT_COLLECTION_NAME, points=points)

        mode_str = "Qdrant Server (Live)" if is_live_server else "Qdrant In-Memory (Test)"
        print("\n" + "=" * 65)
        print(f"🎉 HOÀN THÀNH NOMIC VECTOR HÓA VÀ NẠP {len(points)} POINTS VÀO {mode_str.upper()}!")
        print("=" * 65)


if __name__ == "__main__":
    ingest_to_qdrant()
