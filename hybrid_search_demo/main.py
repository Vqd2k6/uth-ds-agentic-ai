"""
Main Entrypoint Script: Khởi chạy chương trình mô phỏng Hybrid Search (Dense Nomic MoE v2 + BM25 + RRF).
"""
import logging
import sys
from typing import Any, Dict, List

from config import settings
from embeddings import DenseEmbeddingService, SparseEmbeddingService
from qdrant_service import QdrantHybridService

# Thiết lập logging định dạng chuẩn
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("HybridSearchMain")

# Bộ dữ liệu mẫu Đề cương môn học & Quy chế Đại học UTH
SAMPLE_DOCUMENTS: List[Dict[str, Any]] = [
    {
        "text": "Môn học Đại số Tuyến tính (Mã HP: MATH1201) trang bị kiến thức về không gian vector, ma trận, định thức và phép biến đổi tuyến tính.",
        "category": "Đề cương chi tiết",
        "code": "MATH1201"
    },
    {
        "text": "Học phần Xử lý Ngôn ngữ Tự nhiên (NLP - Mã HP: COMP3402) giảng dạy về Tokenization, Word Embeddings, Transformer và RAG Architecture.",
        "category": "Đề cương chi tiết",
        "code": "COMP3402"
    },
    {
        "text": "Quy chế đào tạo theo tín chỉ tại Trường Đại học Giao thông Vận tải TP.HCM (UTH) quy định sinh viên phải hoàn thành tối thiểu 130 tín chỉ.",
        "category": "Quy chế",
        "code": "REG_UTH"
    },
    {
        "text": "Mô hình Nomic Embed Text MoE v2 là mô hình Mixture-of-Experts mã nguồn mở hỗ trợ biểu diễn văn bản ngữ nghĩa đa ngôn ngữ chất lượng cao.",
        "category": "Tài liệu AI",
        "code": "AI_NOMIC"
    },
    {
        "text": "Hệ thống Vector Database Qdrant hỗ trợ cơ chế lưu trữ kết hợp Dense Vector và BM25 Sparse Vector cùng thuật toán RRF Re-ranking.",
        "category": "Tài liệu AI",
        "code": "AI_QDRANT"
    }
]


def run_pipeline():
    logger.info("=== BẮT ĐẦU PIPELINE KHỞI TẠO VÀ CHẠY HYBRID SEARCH ===")

    # 1. Trích xuất nội dung văn bản & metadata
    texts = [doc["text"] for doc in SAMPLE_DOCUMENTS]
    metadatas = [{"category": doc["category"], "code": doc["code"]} for doc in SAMPLE_DOCUMENTS]

    # 2. Khởi tạo các Services
    dense_service = DenseEmbeddingService()
    sparse_service = SparseEmbeddingService()
    qdrant_service = QdrantHybridService(location=":memory:")

    # 3. Trích xuất Embeddings cho Tài liệu
    logger.info("Mã hóa Dense Vectors (Nomic MoE v2)...")
    dense_vectors = dense_service.encode_documents(texts)
    
    logger.info("Mã hóa Sparse Vectors (BM25)...")
    sparse_vectors = sparse_service.encode_documents(texts)

    # 4. Khởi tạo Collection và Index dữ liệu vào Qdrant
    qdrant_service.init_collection()
    qdrant_service.upsert_documents(
        texts=texts,
        dense_vectors=dense_vectors,
        sparse_vectors=sparse_vectors,
        metadatas=metadatas
    )

    # 5. Thử nghiệm các kịch bản Truy vấn
    test_queries = [
        "Sinh viên UTH cần tích lũy bao nhiêu tín chỉ để ra trường?",  # Ngữ nghĩa (Dense + Sparse)
        "COMP3402",                                                    # Từ khóa/Mã HP chính xác (BM25 quyết định)
        "Kiến trúc Mixture of Experts trong biểu diễn văn bản"         # Thuật ngữ chuyên sâu (Nomic MoE v2 quyết định)
    ]

    for q_idx, query in enumerate(test_queries, start=1):
        print(f"\n==================================================")
        print(f"TRUY VẤN THỬ NGHIỆM #{q_idx}: '{query}'")
        print(f"==================================================")

        # Trích xuất Dense & Sparse Vector cho Query
        q_dense = dense_service.encode_query(query)
        q_sparse = sparse_service.encode_query(query)

        # Thực hiện RRF Search trên Qdrant
        search_results = qdrant_service.search_hybrid_rrf(
            query_dense=q_dense,
            query_sparse=q_sparse,
            top_k=settings.top_k_final
        )

        # Hiển thị kết quả
        for rank, res in enumerate(search_results, start=1):
            score = res["score_rrf"]
            payload = res["payload"]
            print(f"\n Top {rank} [Score RRF: {score:.5f}]")
            print(f"   - ID: {res['id']}")
            print(f"   - Mã/Loại: [{payload.get('code')}] ({payload.get('category')})")
            print(f"   - Nội dung: {payload.get('text')}")

    logger.info("=== HOÀN THÀNH PIPELINE THỬ NGHIỆM HYBRID SEARCH ===")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as err:
        logger.critical(f"Chương trình gặp sự cố dừng đột ngột: {err}", exc_info=True)
