"""
Phase 2: Fine-Tuning Execution Script Tối ưu hóa cho Google Colab GPU T4
Huấn luyện nomic-ai/nomic-embed-text-v2-moe trên 2.158 mẫu dataset/final_train_set.jsonl
sử dụng CUDA GPU, Mixed Precision (fp16) và MultipleNegativesRankingLoss.
"""
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List

import torch
from torch.utils.data import DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TrainNomicColab")

BASE_DIR = Path(__file__).parent.parent
WORKSPACE_DATASET_DIR = BASE_DIR / "dataset"
LOCAL_DATASET_DIR = Path(__file__).parent / "dataset"
CHECKPOINTS_DIR = Path(__file__).parent / "checkpoints" / "uth-nomic-embed-v2"
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "nomic-ai/nomic-embed-text-v2-moe"
PREFIX_QUERY = "search_query: "
PREFIX_DOC = "search_document: "


def check_gpu():
    """Kiểm tra môi trường phần cứng GPU trên Google Colab."""
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        logger.info(f"Phát hiện GPU: {gpu_name} (Tổng VRAM: {vram_gb:.2f} GB)")
        return True
    else:
        logger.warning("CẢNH BÁO: Không tìm thấy GPU CUDA! Chương trình sẽ chạy trên CPU (chậm hơn).")
        logger.warning("Hãy bật GPU trong Google Colab: Runtime -> Change runtime type -> Hardware accelerator -> T4 GPU")
        return False


def load_train_dataset() -> List[InputExample]:
    """Tải bộ dữ liệu final_train_set.jsonl (2.158 mẫu chất lượng cao có sẵn query, pos, neg)."""
    examples = []
    
    # 1. Tìm file final_train_set.jsonl trong workspace hoặc thư mục hiện tại
    possible_paths = [
        WORKSPACE_DATASET_DIR / "final_train_set.jsonl",
        Path("dataset/final_train_set.jsonl"),
        Path("final_train_set.jsonl")
    ]
    
    train_file = None
    for p in possible_paths:
        if p.exists():
            train_file = p
            break

    if not train_file:
        logger.error("Không tìm thấy file final_train_set.jsonl! Hãy upload file này lên Colab.")
        sys.exit(1)

    logger.info(f"Đang nạp bộ dữ liệu huấn luyện từ: {train_file.resolve()}")
    with open(train_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                q = f"{PREFIX_QUERY}{item['query']}"
                
                pos_list = item.get("pos", [])
                pos = f"{PREFIX_DOC}{pos_list[0]}" if pos_list else ""
                
                neg_list = item.get("neg", [])
                neg = f"{PREFIX_DOC}{neg_list[0]}" if neg_list else None

                if q and pos:
                    if neg:
                        examples.append(InputExample(texts=[q, pos, neg]))
                    else:
                        examples.append(InputExample(texts=[q, pos]))

    logger.info(f"Đã nạp thành công {len(examples)} mẫu huấn luyện (query, pos, neg).")
    return examples


def train():
    logger.info("=== BẮT ĐẦU TRAINING NOMIC MOE V2 TỐI ƯU CHO COLAB GPU T4 ===")
    has_gpu = check_gpu()

    # 1. Tải mô hình Nomic MoE v2 gốc
    logger.info(f"Đang tải weights mô hình gốc: {MODEL_NAME}...")
    try:
        model = SentenceTransformer(MODEL_NAME, trust_remote_code=True)
        logger.info("Tải mô hình Nomic MoE v2 thành công.")
    except Exception as e:
        logger.error(f"Lỗi khi tải mô hình từ HuggingFace: {e}")
        sys.exit(1)

    # 2. Chuẩn bị DataLoader
    train_examples = load_train_dataset()
    # Batch size 32 tận dụng tối đa 16GB VRAM GPU T4
    batch_size = 32 if has_gpu else 4
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=batch_size)

    # 3. Cấu hình Loss Function (MultipleNegativesRankingLoss - InfoNCE)
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    # 4. Siêu tham số tối ưu (Hyperparameters Tuning)
    epochs = 4
    learning_rate = 2e-5
    warmup_steps = int(len(train_dataloader) * epochs * 0.1)

    logger.info(f"Cấu hình Huấn luyện: Batch Size={batch_size}, Epochs={epochs}, LR={learning_rate}, Warmup Steps={warmup_steps}")
    logger.info("Bắt đầu quá trình huấn luyện (model.fit)...")

    try:
        model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            optimizer_params={"lr": learning_rate},
            weight_decay=0.01,
            output_path=str(CHECKPOINTS_DIR),
            show_progress_bar=True,
            use_amp=has_gpu  # Automatic Mixed Precision (fp16) tăng tốc 2.5x trên T4 GPU
        )
        logger.info(f"Đã xuất weights mô hình hoàn chỉnh tại: {CHECKPOINTS_DIR}")
        
        # Tự động nén zip checkpoints để tải về máy dễ dàng trên Colab
        zip_path = Path(__file__).parent / "uth-nomic-embed-v2.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", CHECKPOINTS_DIR)
        logger.info(f"Đã nén file zip sẵn sàng tải về: {zip_path}")
        
        logger.info("=== HOÀN THÀNH HUẤN LUYỆN TRÊN COLAB T4 GPU ===")
    except Exception as err:
        logger.critical(f"Sự cố trong quá trình huấn luyện: {err}", exc_info=True)


if __name__ == "__main__":
    train()
