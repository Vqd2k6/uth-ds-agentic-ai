"""
Phase 3: Model Evaluation Script Tối ưu cho Colab & Local
Đo lường và so sánh chỉ số MRR@10 & NDCG@10 giữa Mô hình Gốc và Mô hình Fine-tuned.
"""
import json
import logging
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer, util

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EvaluateModel")

BASE_DIR = Path(__file__).parent.parent
WORKSPACE_DATASET_DIR = BASE_DIR / "dataset"
LOCAL_DATASET_DIR = Path(__file__).parent / "dataset"
CHECKPOINTS_DIR = Path(__file__).parent / "checkpoints" / "uth-nomic-embed-v2"
BASE_MODEL_NAME = "nomic-ai/nomic-embed-text-v2-moe"

PREFIX_QUERY = "search_query: "
PREFIX_DOC = "search_document: "


def load_test_dataset() -> Tuple[List[str], List[str]]:
    """Tải tập dữ liệu kiểm thử, hỗ trợ tìm kiếm linh hoạt ở mọi vị trí trên Colab và Local."""
    queries = []
    docs = []

    # Các đường dẫn khả thi của final_val_set.jsonl
    possible_val_paths = [
        WORKSPACE_DATASET_DIR / "final_val_set.jsonl",
        Path("dataset/final_val_set.jsonl"),
        Path("final_val_set.jsonl"),
        Path("../dataset/final_val_set.jsonl"),
        Path("fine-tune-nomic/dataset/final_val_set.jsonl"),
        Path("/content/dataset/final_val_set.jsonl"),
        Path("/content/final_val_set.jsonl")
    ]

    val_file = next((p for p in possible_val_paths if p.exists()), None)
    if val_file:
        logger.info(f"Đã nạp tập validation từ: {val_file.resolve()}")
        with open(val_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    q = item.get("query", "")
                    pos_list = item.get("pos", [])
                    if q and pos_list:
                        queries.append(f"{PREFIX_QUERY}{q}")
                        docs.append(f"{PREFIX_DOC}{pos_list[0]}")
        logger.info(f"Đã tải thành công {len(queries)} mẫu test từ final_val_set.jsonl.")
        return queries, docs

    # Thử nạp từ test_pairs.json (nếu có)
    possible_test_paths = [
        LOCAL_DATASET_DIR / "test_pairs.json",
        Path("dataset/test_pairs.json"),
        Path("test_pairs.json"),
        Path("../dataset/test_pairs.json")
    ]
    test_file = next((p for p in possible_test_paths if p.exists()), None)
    if test_file:
        logger.info(f"Đã nạp tập test từ: {test_file.resolve()}")
        with open(test_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        queries = [item["query"] for item in data]
        docs = [item["positive_doc"] for item in data]
        logger.info(f"Đã tải {len(queries)} mẫu test từ test_pairs.json.")
        return queries, docs

    logger.error("Không tìm thấy file final_val_set.jsonl hoặc test_pairs.json!")
    logger.error("Hãy đảm bảo bạn đã upload file final_val_set.jsonl vào thư mục dataset/ hoặc thư mục làm việc hiện tại.")
    sys.exit(1)


def evaluate_embedding_model(model_path_or_name: str, queries: List[str], docs: List[str], top_k: int = 10) -> Dict[str, float]:
    """Tính toán chỉ số MRR@K và NDCG@K trên danh sách queries và docs."""
    logger.info(f"Đang đánh giá mô hình: {model_path_or_name}...")
    model = SentenceTransformer(model_path_or_name, trust_remote_code=True)

    query_embeddings = model.encode(queries, convert_to_tensor=True)
    doc_embeddings = model.encode(docs, convert_to_tensor=True)

    mrr_scores = []
    ndcg_scores = []

    for i in range(len(queries)):
        q_emb = query_embeddings[i]
        scores = util.cos_sim(q_emb, doc_embeddings)[0].cpu().numpy()
        top_indices = np.argsort(-scores)[:top_k]
        
        rank = -1
        for r, idx in enumerate(top_indices, start=1):
            if idx == i:
                rank = r
                break

        if rank != -1:
            mrr_scores.append(1.0 / rank)
            ndcg_scores.append(1.0 / math.log2(rank + 1))
        else:
            mrr_scores.append(0.0)
            ndcg_scores.append(0.0)

    return {"MRR@10": float(np.mean(mrr_scores)), "NDCG@10": float(np.mean(ndcg_scores))}


def run_evaluation():
    logger.info("=== BẮT ĐẦU ĐÁNH GIÁ VÀ SO SÁNH HIỆU NĂNG MÔ HÌNH ===")
    queries, docs = load_test_dataset()

    base_results = evaluate_embedding_model(BASE_MODEL_NAME, queries, docs)
    
    # Tìm checkpoints directory linh hoạt
    possible_ckpt_paths = [
        CHECKPOINTS_DIR,
        Path("checkpoints/uth-nomic-embed-v2"),
        Path("fine-tune-nomic/checkpoints/uth-nomic-embed-v2"),
        Path("/content/fine-tune-nomic/checkpoints/uth-nomic-embed-v2")
    ]
    ckpt_path = next((p for p in possible_ckpt_paths if p.exists()), None)

    if ckpt_path:
        ft_results = evaluate_embedding_model(str(ckpt_path), queries, docs)
    else:
        logger.warning(f"Chưa tìm thấy mô hình fine-tuned tại checkpoints/uth-nomic-embed-v2. Chỉ in kết quả mô hình gốc.")
        ft_results = None

    print("\n==================================================")
    print("BẢNG SO SÁNH CHỈ SỐ ĐÁNH GIÁ (RETRIEVAL BENCHMARK)")
    print("==================================================")
    print(f"Mô hình Gốc ({BASE_MODEL_NAME}):")
    print(f"  - MRR@10:  {base_results['MRR@10']:.4f}")
    print(f"  - NDCG@10: {base_results['NDCG@10']:.4f}")

    if ft_results:
        print(f"\nMô hình Fine-tuned UTH ({ckpt_path.name}):")
        print(f"  - MRR@10:  {ft_results['MRR@10']:.4f}")
        print(f"  - NDCG@10: {ft_results['NDCG@10']:.4f}")
        
        mrr_diff = ((ft_results['MRR@10'] - base_results['MRR@10']) / base_results['MRR@10']) * 100
        ndcg_diff = ((ft_results['NDCG@10'] - base_results['NDCG@10']) / base_results['NDCG@10']) * 100
        print(f"\nMức độ Cải thiện:")
        print(f"  - MRR@10:  +{mrr_diff:.2f}%")
        print(f"  - NDCG@10: +{ndcg_diff:.2f}%")

    logger.info("=== HOÀN THÀNH PHASE 3: ĐÁNH GIÁ MÔ HÌNH ===")


if __name__ == "__main__":
    run_evaluation()
