#!/usr/bin/env python3
"""
Script Dựng Đồ thị Tri thức Knowledge Graph trên Neo4j (GraphDB).
Tạo các Nút (Nodes) Môn học, CLO, PLO và các Cạnh (Edges) thể hiện mối quan hệ.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
JSON_COLLECTIONS_DIR = PROJECT_DIR / "structuring_data" / "json_collections"

SUBJECTS_FILE = JSON_COLLECTIONS_DIR / "syllabus_subjects.json"
FRAMEWORKS_FILE = JSON_COLLECTIONS_DIR / "outcome_frameworks.json"

sys.path.append(str(BASE_DIR))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


def clean_str(s: str) -> str:
    """Loại bỏ ký tự nháy đơn và backslash để tránh lỗi Cypher"""
    if not s:
        return ""
    return s.replace("'", "").replace("\\", "")


def load_json(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        print(f"[!] Không tìm thấy file: {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data if isinstance(data, list) else [data]


def ingest_to_neo4j():
    """Dựng Đồ thị Tri thức Môn học - CLO - PLO trên Neo4j"""
    print("=" * 65)
    print("🌐 BẮT ĐẦU PIPELINE DỰNG KNOWLEDGE GRAPH TRÊN NEO4J")
    print("=" * 65)
    print(f"  - Neo4j URI:  {NEO4J_URI}")
    print(f"  - Username:   {NEO4J_USER}")
    print("=" * 65 + "\n")

    subjects = load_json(SUBJECTS_FILE)
    frameworks = load_json(FRAMEWORKS_FILE)

    if not subjects or not frameworks:
        print("[!] Thiếu dữ liệu đầu vào để dựng Đồ thị.")
        return

    driver = None
    is_connected = False

    if NEO4J_AVAILABLE:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            driver.verify_connectivity()
            is_connected = True
            print(f"[✓] Kết nối Neo4j Server thành công tại {NEO4J_URI}!\n")
        except Exception:
            print(f"[!] Không thể kết nối tới Neo4j Server tại {NEO4J_URI}.")
            print("    Mẹo: Bạn có thể bật Docker bằng lệnh: cd database_ingestion && docker compose up -d")
            print("    Script sẽ tiếp tục ở chế độ Kiểm thử Cypher (Dry-run Mode).\n")
            is_connected = False

    cypher_queries = []

    # 1. Tạo Nút PO & Nút PLO từ outcome_frameworks
    framework = frameworks[0]
    pos = framework.get("pos", [])
    plos = framework.get("plos", [])
    matrix = framework.get("course_contribution_plo_matrix", [])

    for po in pos:
        po_id = clean_str(po["po_id"])
        desc = clean_str(po["description"])
        cypher = f"MERGE (p:PO {{po_id: '{po_id}'}}) SET p.description = '{desc}'"
        cypher_queries.append(cypher)

    for plo in plos:
        plo_id = clean_str(plo["plo_id"])
        desc = clean_str(plo["description"])
        cat = clean_str(plo.get("category", ""))
        cypher = f"MERGE (p:PLO {{plo_id: '{plo_id}'}}) SET p.description = '{desc}', p.category = '{cat}'"
        cypher_queries.append(cypher)

    # 2. Tạo Nút Môn học, Nút CLO, Nút Giáo trình và Cạnh liên kết
    for subj in subjects:
        code = clean_str(subj.get("subject_code", ""))
        name = clean_str(subj.get("subject_name_vi", ""))
        credits = subj.get("credits", 3)

        cypher_subj = f"MERGE (c:Course {{subject_code: '{code}'}}) SET c.name = '{name}', c.credits = {credits}"
        cypher_queries.append(cypher_subj)

        # Cạnh CLO
        for clo in subj.get("clos", []):
            clo_code = clean_str(clo['clo_code'])
            clo_id = f"{code}_{clo_code}"
            clo_desc = clean_str(clo["description"])
            cypher_clo = f"MERGE (clo:CLO {{clo_id: '{clo_id}'}}) SET clo.code = '{clo_code}', clo.description = '{clo_desc}' WITH clo MATCH (c:Course {{subject_code: '{code}'}}) MERGE (c)-[:HAS_CLO]->(clo)"
            cypher_queries.append(cypher_clo)

        # Cạnh Giáo trình chính
        for idx, book in enumerate(subj.get("main_textbooks", []), 1):
            book_title = clean_str(book[:100])
            book_id = f"{code}_book_{idx}"
            cypher_book = f"MERGE (b:Textbook {{book_id: '{book_id}'}}) SET b.title = '{book_title}' WITH b MATCH (c:Course {{subject_code: '{code}'}}) MERGE (c)-[:USES_TEXTBOOK]->(b)"
            cypher_queries.append(cypher_book)

        # Cạnh Môn học trước / Tiên quyết
        for prev_code in subj.get("previous_subject_codes", []):
            clean_prev = clean_str(prev_code)
            cypher_prev = f"MATCH (c:Course {{subject_code: '{code}'}}), (prev:Course {{subject_code: '{clean_prev}'}}) MERGE (c)-[:REQUIRES_PREVIOUS]->(prev)"
            cypher_queries.append(cypher_prev)

    # 3. Tạo Cạnh Ma trận Đóng góp (:Course)-[:CONTRIBUTES_TO]->(:PLO)
    for item in matrix:
        subj_code = clean_str(item["subject_code"])
        plo_id = clean_str(item["plo_id"])
        level = clean_str(item["contribution_level"])
        cypher_rel = f"MATCH (c:Course {{subject_code: '{subj_code}'}}), (p:PLO {{plo_id: '{plo_id}'}}) MERGE (c)-[r:CONTRIBUTES_TO]->(p) SET r.level = '{level}'"
        cypher_queries.append(cypher_rel)

    # Chạy các câu truy vấn Cypher nếu server live
    if is_connected and driver:
        with driver.session() as session:
            for q in cypher_queries:
                session.run(q)
        print(f"[✓] Đã thực thi {len(cypher_queries)} câu lệnh Cypher dựng Đồ thị tri thức hoàn chỉnh!")
        driver.close()
    else:
        print(f"--- KIỂM THỬ CYPHER GENERATION (DRY-RUN) ---")
        print(f"  [✓] Đã tạo thành công {len(cypher_queries)} câu lệnh Cypher hợp lệ.")
        print(f"  [✓] Đã cấu hình {len(plos)} Nút PLO, {len(subjects)} Nút Course, và Ma trận Đóng góp.")
        print("--------------------------------------------")

    print("\n" + "=" * 65)
    print("🎉 HOÀN THÀNH PIPELINE DỰNG ĐỒ THỊ TRI THỨC KNOWLEDGE GRAPH!")
    print("=" * 65)


if __name__ == "__main__":
    ingest_to_neo4j()
