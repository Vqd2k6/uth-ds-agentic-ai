#!/usr/bin/env python3
"""
Master Runner nạp dữ liệu tự động cho cả 3 CSDL (MongoDB, Qdrant Vector DB, Neo4j Graph).
"""

import sys
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
VENV_PYTHON = SCRIPTS_DIR.parent.parent / ".venv" / "bin" / "python"


def run_script(script_name: str):
    script_path = SCRIPTS_DIR / script_name
    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU NẠP DỮ LIỆU: {script_name}")
    print(f"=======================================================")
    
    try:
        subprocess.run([str(VENV_PYTHON), str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Lỗi khi thực thi {script_name}: {e}")
        sys.exit(1)


def main():
    print("=" * 65)
    print("🌟 BẮT ĐẦU QUY TRÌNH NẠP DỮ LIỆU TỰ ĐỘNG (AUTOMATED DATA INGESTION)")
    print("=" * 65)
    
    # 1. Nạp MongoDB
    run_script("ingest_mongodb.py")
    
    # 2. Nạp Qdrant Vector DB (Nomic Embeddings 768-dim)
    run_script("ingest_qdrant.py")
    
    # 3. Nạp Neo4j Knowledge Graph
    run_script("ingest_neo4j.py")
    
    print("\n" + "=" * 65)
    print("🎉 HOÀN THÀNH TOÀN BỘ PIPELINE NẠP DỮ LIỆU VÀO 3 CSDL!")
    print("=" * 65)


if __name__ == "__main__":
    main()
