#!/usr/bin/env python3
"""
Graph Knowledge Retriever truy vấn Đồ thị Tri thức Neo4j (GraphRAG).
Hỗ trợ truy vấn mối quan hệ giữa Môn học ↔ CLO ↔ PLO.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

sys.path.append(str(PROJECT_DIR / "database_ingestion"))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class GraphRetriever:
    def __init__(self):
        self.driver = None
        if NEO4J_AVAILABLE:
            try:
                self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
                self.driver.verify_connectivity()
            except Exception:
                self.driver = None

    def query_subject_clos_and_plos(self, subject_code: str) -> List[Dict[str, Any]]:
        """Truy vấn các CLO của môn học và các PLO mà môn học đó đóng góp trên Neo4j"""
        if not self.driver:
            return []

        cypher = """
        MATCH (c:Course {subject_code: $code})-[:HAS_CLO]->(clo:CLO)
        OPTIONAL MATCH (c)-[r:CONTRIBUTES_TO]->(p:PLO)
        RETURN c.subject_code AS subject_code,
               c.name AS subject_name,
               clo.code AS clo_code,
               clo.description AS clo_description,
               p.plo_id AS plo_id,
               p.description AS plo_description,
               r.level AS contribution_level
        """
        
        results = []
        try:
            with self.driver.session() as session:
                res = session.run(cypher, code=subject_code)
                for record in res:
                    results.append(dict(record))
            return results
        except Exception as e:
            print(f"[!] Lỗi truy vấn Neo4j Graph: {e}")
            return []

    def close(self):
        if self.driver:
            self.driver.close()


if __name__ == "__main__":
    retriever = GraphRetriever()
    res = retriever.query_subject_clos_and_plos("124100")
    print(f"[*] Kết quả truy vấn Neo4j Graph cho môn 124100 ({len(res)} bản ghi):")
    for r in res:
        print(f"  - CLO: {r.get('clo_code')} -> PLO: {r.get('plo_id')} ({r.get('contribution_level')})")
    retriever.close()
