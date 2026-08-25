#!/usr/bin/env python3
"""
Pipeline bóc tách PDF Đề cương học phần sử dụng MinerU (Magic-PDF)
Hỗ trợ tăng tốc GPU Apple Silicon (MPS) và xử lý đa tiến trình song song (Multiprocessing).
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed

# Thiết lập đường dẫn thư mục mặc định
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_PDF_DIR = BASE_DIR / "raw_pdfs"
OUTPUT_DIR = BASE_DIR / "parsed_output"
VENV_PYTHON = BASE_DIR.parent / ".venv" / "bin" / "python"
VENV_MAGIC_PDF = BASE_DIR.parent / ".venv" / "bin" / "magic-pdf"


def check_environment():
    """Kiểm tra môi trường và file cấu hình magic-pdf.json"""
    home_config = Path.home() / "magic-pdf.json"
    local_config = BASE_DIR / "magic-pdf.json"
    
    if not home_config.exists() and local_config.exists():
        import shutil
        shutil.copy2(local_config, home_config)
        print(f"[*] Đã sao chép file cấu hình vào: {home_config}")

    if not VENV_MAGIC_PDF.exists():
        print(f"[!] Không tìm thấy thực thi magic-pdf tại: {VENV_MAGIC_PDF}")
        sys.exit(1)


def parse_single_pdf_worker(args_tuple: Tuple[str, str, str, Optional[int], Optional[int], bool]) -> Tuple[str, bool, float, str]:
    """
    Worker độc lập để parse 1 file PDF trong một process riêng biệt
    """
    pdf_path_str, output_base_dir_str, method, start_page, end_page, debug = args_tuple
    pdf_path = Path(pdf_path_str)
    output_base_dir = Path(output_base_dir_str)
    
    cmd = [
        str(VENV_MAGIC_PDF),
        "-p", str(pdf_path),
        "-o", str(output_base_dir),
        "-m", method,
    ]
    
    if start_page is not None:
        cmd.extend(["-s", str(start_page)])
    if end_page is not None:
        cmd.extend(["-e", str(end_page)])
    if debug:
        cmd.extend(["-d", "true"])

    start_time = time.time()
    try:
        process = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        elapsed = time.time() - start_time
        return (pdf_path.name, True, elapsed, "")
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        err_msg = e.output if e.output else "Lỗi không xác định"
        return (pdf_path.name, False, elapsed, err_msg)
    except Exception as e:
        elapsed = time.time() - start_time
        return (pdf_path.name, False, elapsed, str(e))


def run_batch_parallel(
    raw_dir: Path,
    output_dir: Path,
    method: str = "txt",
    force: bool = False,
    limit: Optional[int] = None,
    max_workers: int = 3
):
    """
    Chạy bóc tách hàng loạt đa tiến trình song song
    """
    pdf_files = sorted(list(raw_dir.glob("*.pdf")))
    if not pdf_files:
        print(f"[!] Không tìm thấy file PDF nào trong: {raw_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    
    if limit is not None:
        pdf_files = pdf_files[:limit]

    # Lọc danh sách các file cần parse
    tasks = []
    skipped_files = []
    
    for pdf_path in pdf_files:
        subject_name = pdf_path.stem
        subject_output = output_dir / subject_name
        
        md_files = list(subject_output.glob("**/*.md")) if subject_output.exists() else []
        if md_files and not force:
            skipped_files.append(pdf_path.name)
        else:
            tasks.append((str(pdf_path), str(output_dir), method, None, None, False))

    total_all = len(pdf_files)
    total_to_run = len(tasks)
    
    print("=" * 65)
    print("🚀 BẮT ĐẦU PARSE HÀNG LOẠT (ĐA TIẾN TRÌNH + GPU MPS)")
    print("=" * 65)
    print(f"  - Tổng số file:      {total_all}")
    print(f"  - Đã có sẵn (bỏ qua): {len(skipped_files)}")
    print(f"  - Cần xử lý:        {total_to_run}")
    print(f"  - Số tiến trình song song (Workers): {max_workers}")
    print(f"  - Chế độ parse:     {method}")
    print("=" * 65 + "\n")

    if total_to_run == 0:
        print("[✓] Toàn bộ file đã được bóc tách trước đó. Không có file nào cần chạy thêm!")
        return

    success_count = 0
    fail_count = 0
    total_start = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(parse_single_pdf_worker, t): t[0] for t in tasks}
        
        completed_idx = 0
        for future in as_completed(futures):
            completed_idx += 1
            file_name, success, elapsed, err_msg = future.result()
            
            if success:
                success_count += 1
                print(f"[{completed_idx}/{total_to_run}] [✓ THÀNH CÔNG] {file_name} ({elapsed:.1f}s)")
            else:
                fail_count += 1
                print(f"[{completed_idx}/{total_to_run}] [✗ THẤT BẠI]   {file_name} ({elapsed:.1f}s)")
                if err_msg:
                    print(f"    [!] Lỗi: {err_msg[:200]}...")

    total_elapsed = time.time() - total_start
    print("\n" + "=" * 65)
    print("                   TỔNG KẾT TIẾN TRÌNH")
    print("=" * 65)
    print(f"  - Thành công:       {success_count}/{total_to_run}")
    print(f"  - Thất bại:         {fail_count}/{total_to_run}")
    print(f"  - Bỏ qua có sẵn:   {len(skipped_files)}")
    print(f"  - Tổng thời gian:   {total_elapsed:.1f}s (~{total_elapsed/60:.2f} phút)")
    if success_count > 0:
        avg_time = total_elapsed / success_count
        print(f"  - Tốc độ trung bình: {avg_time:.1f}s / file")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description="MinerU PDF Parser Tối Ưu cho Đề cương UTH")
    parser.add_argument("--file", "-f", type=str, help="Tên file PDF cụ thể cần parse (trong raw_pdfs)")
    parser.add_argument("--all", "-a", action="store_true", help="Parse toàn bộ file trong raw_pdfs")
    parser.add_argument("--method", "-m", choices=["auto", "txt", "ocr"], default="txt", help="Phương thức parse (mặc định: txt)")
    parser.add_argument("--workers", "-w", type=int, default=3, help="Số tiến trình song song (mặc định: 3)")
    parser.add_argument("--force", action="store_true", help="Parse lại kể cả khi đã có kết quả")
    parser.add_argument("--limit", "-l", type=int, default=None, help="Giới hạn số lượng file parse")
    parser.add_argument("--start-page", "-s", type=int, default=None, help="Trang bắt đầu (0-indexed)")
    parser.add_argument("--end-page", "-e", type=int, default=None, help="Trang kết thúc (0-indexed)")
    parser.add_argument("--debug", "-d", action="store_true", help="Bật chế độ debug chi tiết")

    args = parser.parse_args()

    check_environment()

    if args.file:
        target_path = RAW_PDF_DIR / args.file
        if not target_path.exists():
            target_path = Path(args.file)
        if not target_path.exists():
            print(f"[!] Không tìm thấy file: {args.file}")
            sys.exit(1)
        name, success, elapsed, err = parse_single_pdf_worker(
            (str(target_path), str(OUTPUT_DIR), args.method, args.start_page, args.end_page, args.debug)
        )
        if success:
            print(f"[✓] Thành công: {name} trong {elapsed:.2f}s")
        else:
            print(f"[✗] Thất bại: {name}\nLỗi: {err}")
    else:
        run_batch_parallel(
            RAW_PDF_DIR,
            OUTPUT_DIR,
            method=args.method,
            force=args.force,
            limit=args.limit,
            max_workers=args.workers
        )


if __name__ == "__main__":
    main()
