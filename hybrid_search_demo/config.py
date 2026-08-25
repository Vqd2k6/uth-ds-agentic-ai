"""
Cấu hình hệ thống Hybrid Search Qdrant và Model Embeddings.
"""
from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Cấu hình Collection Qdrant
    collection_name: str = Field(default="uth_hybrid_knowledge", description="Tên Collection trong Qdrant")
    
    # Cấu hình Mô hình Dense Embedding
    dense_model_name: str = Field(default="nomic-ai/nomic-embed-text-v2-moe", description="Họ mô hình Nomic MoE v2")
    dense_vector_name: str = Field(default="dense-nomic", description="Tên định danh Dense Vector")
    dense_vector_size: int = Field(default=768, description="Số chiều của Nomic MoE v2 Dense Vector")
    prefix_document: str = Field(default="search_document: ", description="Tiền tố cho tài liệu lưu trữ")
    prefix_query: str = Field(default="search_query: ", description="Tiền tố cho câu truy vấn")

    # Cấu hình Mô hình Sparse Embedding (BM25)
    sparse_model_name: str = Field(default="Qdrant/bm25", description="Mô hình FastEmbed BM25 thưa")
    sparse_vector_name: str = Field(default="sparse-bm25", description="Tên định danh Sparse Vector")

    # Cấu hình RRF & Retrieval
    top_k_prefetch: int = Field(default=10, description="Số lượng kết quả lấy từ mỗi luồng (Dense/Sparse) trước khi RRF")
    top_k_final: int = Field(default=3, description="Số lượng kết quả trả về cuối cùng sau RRF")


# Instantiation singleton settings
settings = Settings()
