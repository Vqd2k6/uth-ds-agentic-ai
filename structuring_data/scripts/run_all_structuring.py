#!/usr/bin/env python3
"""
Master runner cho module structuring_data.
Chạy lần lượt tất cả 4 kịch bản trích xuất Schema và tạo Chunks.
"""

import sys
import subprocess
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
VENV_PYTHON = SCRIPTS_DIR.parent.parent / ".venv" / "bin" / "python"


def run_script(script_name: str):
    script_path = SCRIPTS_DIR / script_name
    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU CHẠY: {script_name}")
    print(f"=======================================================")
    
    try:
        subprocess.run([str(VENV_PYTHON), str(script_path)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Lỗi khi chạy {script_name}: {e}")
        sys.exit(1)


def main():
    run_script("extract_subjects.py")
    run_script("extract_frameworks.py")
    run_script("extract_rubrics.py")
    run_script("extract_chunks.py")
    
    print("\n" + "=" * 65)
    print("🎉 HOÀN THÀNH TOÀN BỘ PIPELINE TRÍCH XUẤT 4 JSON COLLECTIONS!")
    print("=" * 65)


if __name__ == "__main__":
    main()
