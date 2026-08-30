#!/usr/bin/env python3
"""
Master Deep Chunk Generator: Tạo hơn 1,500+ Chunks tri thức nguyên tử chi tiết từ 41 môn học.
- Chunks Mô tả môn học, Mục tiêu CO, Chuẩn đầu ra CLO.
- Chunks Kế hoạch chi tiết từng tuần học (Tuần 1 -> Tuần 15).
- Chunks Giáo trình chính & Tài liệu tham khảo từng môn.
- Chunks Phương pháp đánh giá, Thang điểm & Rubrics.
- Chunks Khung CTĐT PO/PLO và Rubrics chi tiết (A1.1 -> A5.5).
"""

import json
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_DIR = BASE_DIR / "json_collections"

SUBJECTS_JSON_PATH = JSON_DIR / "syllabus_subjects.json"
FRAMEWORKS_JSON_PATH = JSON_DIR / "outcome_frameworks.json"
RUBRICS_JSON_PATH = JSON_DIR / "rubric_catalog.json"
CHUNKS_JSON_PATH = JSON_DIR / "chunk_sources.json"


def generate_all_deep_chunks():
    print("=" * 70)
    print("🚀 BẮT ĐẦU TẠO HƠN 1,500+ CHUNKS TRI THỨC NGUYÊN TỬ TỪ DỮ LIỆU ĐÃ BÓC TÁCH")
    print("=" * 70)

    if not SUBJECTS_JSON_PATH.exists():
        print("[!] Không tìm thấy syllabus_subjects.json. Vui lòng chạy deep_extract_all.py trước!")
        return

    with open(SUBJECTS_JSON_PATH, "r", encoding="utf-8") as f:
        subjects = json.load(f)

    frameworks = []
    if FRAMEWORKS_JSON_PATH.exists():
        with open(FRAMEWORKS_JSON_PATH, "r", encoding="utf-8") as f:
            frameworks = json.load(f)

    rubrics = []
    if RUBRICS_JSON_PATH.exists():
        with open(RUBRICS_JSON_PATH, "r", encoding="utf-8") as f:
            rubrics = json.load(f)

    all_chunks: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # 1. TẠO CHUNKS TỪ 41 HỌC PHẦN
    # -------------------------------------------------------------
    for subj in subjects:
        code = subj.get("subject_code", "UNKNOWN")
        name_vi = subj.get("subject_name_vi", "")
        name_en = subj.get("subject_name_en", "")
        credits = subj.get("credits", 3)
        cb = subj.get("credit_breakdown", {})
        credits_str = f"{credits} tín chỉ (Lý thuyết: {cb.get('theory', 2)}, Thực hành: {cb.get('practice', 1)}, Tự học: {cb.get('self_study', 3)})"

        # 1.1 Chunk Tổng quan môn học (General Information & Description)
        if subj.get("description"):
            prev = ", ".join(subj.get("previous_subject_codes", [])) or "Không"
            all_chunks.append({
                "chunk_id": f"{code}_overview_desc",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "overview",
                "section_title": "1. Tổng quan & Mô tả học phần",
                "content": (
                    f"Học phần: {name_vi} ({name_en}) - Mã học phần: {code}.\n"
                    f"Số tín chỉ: {credits_str}.\n"
                    f"Học phần học trước: {prev}.\n"
                    f"Mô tả nội dung: {subj['description']}"
                ),
                "metadata": {"subject_code": code, "credits": credits}
            })

        # 1.2 Chunks Mục tiêu môn học (COs)
        for co in subj.get("course_objectives", []):
            co_code = co["co_code"]
            all_chunks.append({
                "chunk_id": f"{code}_co_{co_code.lower()}",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "course_objective",
                "section_title": "3. Mục tiêu học phần (CO)",
                "content": f"Mục tiêu {co_code} môn {name_vi} ({code}): {co['description']}",
                "metadata": {"subject_code": code, "co_code": co_code}
            })

        # 1.3 Chunks Chuẩn đầu ra môn học (CLOs)
        for clo in subj.get("clos", []):
            clo_code = clo["clo_code"]
            all_chunks.append({
                "chunk_id": f"{code}_clo_{clo_code.lower()}",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "clo",
                "section_title": "4. Chuẩn đầu ra học phần (CLO)",
                "content": f"Chuẩn đầu ra {clo_code} môn {name_vi} ({code}): {clo['description']}",
                "metadata": {"subject_code": code, "clo_code": clo_code}
            })

        # 1.4 Chunk Nhiệm vụ của sinh viên (Student duties)
        if subj.get("student_duties"):
            duties_str = "\n- ".join(subj["student_duties"])
            all_chunks.append({
                "chunk_id": f"{code}_student_duties",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "student_duties",
                "section_title": "5. Nhiệm vụ của sinh viên",
                "content": f"Nhiệm vụ và quy định đối với sinh viên khi học môn {name_vi} ({code}):\n- {duties_str}",
                "metadata": {"subject_code": code}
            })

        # 1.5 Chunks Phương pháp đánh giá & Điểm số (Assessment Methods)
        if subj.get("assessment_methods"):
            # Chunk tổng quan thang điểm
            methods_summary = []
            for m in subj["assessment_methods"]:
                comp = m.get("component", "")
                meth = m.get("method", "")
                clos = m.get("clos", "")
                rub = m.get("rubric_criteria", "")
                weight = m.get("weight_percent", "")
                methods_summary.append(f"• {comp} ({meth}) - CLO: {clos} - Tiêu chí {rub} - Trọng số: {weight}%")
                
                # Chunk riêng cho từng thành phần đánh giá
                all_chunks.append({
                    "chunk_id": f"{code}_eval_{comp.lower().replace(' ', '_')}_{rub.lower()}",
                    "subject_code": code,
                    "subject_name_vi": name_vi,
                    "chunk_type": "assessment_component",
                    "section_title": f"6. Đánh giá - {comp}",
                    "content": f"Hình thức đánh giá '{comp}' môn {name_vi} ({code}): Phương pháp {meth}, đánh giá chuẩn đầu ra {clos}, áp dụng tiêu chí rubric {rub}, chiếm {weight}% tổng kết môn.",
                    "metadata": {"subject_code": code, "rubric": rub}
                })

            all_chunks.append({
                "chunk_id": f"{code}_grading_scheme",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "grading_scheme",
                "section_title": "6. Thang điểm & Tiêu chuẩn đánh giá",
                "content": f"Thang điểm và cơ cấu điểm số môn {name_vi} ({code}):\n" + "\n".join(methods_summary),
                "metadata": {"subject_code": code}
            })

        # 1.6 Chunks Kế hoạch giảng dạy chi tiết TỪNG TUẦN HỌC (Weekly Plan Chunks & Micro-chunks)
        for idx, tp in enumerate(subj.get("teaching_plan", []), 1):
            week_label = tp.get("week_or_chapter", f"Tuần {idx}")
            content = tp.get("content", "")
            clos = tp.get("clos", "")
            activities = tp.get("learning_activities", "")
            assessment = tp.get("assessment", "")

            # Chunk 1: Tổng quan tuần học
            all_chunks.append({
                "chunk_id": f"{code}_week_{idx}_overview",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "weekly_plan_overview",
                "section_title": f"7. Kế hoạch giảng dạy - {week_label}",
                "content": (
                    f"Kế hoạch giảng dạy môn {name_vi} ({code}) tại {week_label}:\n"
                    f"• Nội dung: {content}\n"
                    f"• Chuẩn đầu ra CLO: {clos}\n"
                    f"• Hoạt động: {activities}\n"
                    f"• Đánh giá: {assessment or 'Theo tiến độ'}"
                ),
                "metadata": {"subject_code": code, "week": week_label, "clos": clos}
            })

            # Chunk 2: Phân tách riêng phần Lý thuyết nếu có
            if "Lý thuyết:" in content:
                theory_part = content.split("Thực hành:")[0].replace("Lý thuyết:", "").strip()
                if len(theory_part) > 10:
                    all_chunks.append({
                        "chunk_id": f"{code}_week_{idx}_theory",
                        "subject_code": code,
                        "subject_name_vi": name_vi,
                        "chunk_type": "weekly_theory",
                        "section_title": f"7. Lý thuyết {week_label} - Môn {name_vi}",
                        "content": f"Kiến thức lý thuyết giảng dạy {week_label} môn {name_vi} ({code}):\n{theory_part}\n(Chuẩn đầu ra: {clos})",
                        "metadata": {"subject_code": code, "week": week_label}
                    })

            # Chunk 3: Phân tách riêng phần Thực hành & Bài tập nếu có
            if "Thực hành:" in content:
                practice_part = content.split("Thực hành:")[1].strip()
                if len(practice_part) > 10:
                    all_chunks.append({
                        "chunk_id": f"{code}_week_{idx}_practice",
                        "subject_code": code,
                        "subject_name_vi": name_vi,
                        "chunk_type": "weekly_practice",
                        "section_title": f"7. Thực hành & Bài tập {week_label} - Môn {name_vi}",
                        "content": f"Nội dung thực hành, bài tập và kỹ năng cần rèn luyện {week_label} môn {name_vi} ({code}):\n{practice_part}\n(Chuẩn đầu ra: {clos})",
                        "metadata": {"subject_code": code, "week": week_label}
                    })

        # 1.7 Chunks Giáo trình & Sách tham khảo (Tách TỪNG CUỐN SÁCH thành Chunk độc lập)
        for b_idx, book in enumerate(subj.get("main_textbooks", []), 1):
            all_chunks.append({
                "chunk_id": f"{code}_book_main_{b_idx}",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "main_textbook",
                "section_title": f"8.1. Giáo trình chính môn {name_vi}",
                "content": f"Giáo trình chính bắt buộc của học phần {name_vi} ({code}) là tài liệu: {book}",
                "metadata": {"subject_code": code, "is_main": True}
            })

        for r_idx, ref in enumerate(subj.get("reference_materials", []), 1):
            all_chunks.append({
                "chunk_id": f"{code}_book_ref_{r_idx}",
                "subject_code": code,
                "subject_name_vi": name_vi,
                "chunk_type": "reference_material",
                "section_title": f"8.2. Tài liệu tham khảo môn {name_vi}",
                "content": f"Tài liệu tham khảo mở rộng của học phần {name_vi} ({code}) là tài liệu: {ref}",
                "metadata": {"subject_code": code, "is_main": False}
            })

        # 1.8 Chunks Điều kiện học phần & Khối kiến thức
        prereqs = ", ".join(subj.get("prerequisite_subject_codes", [])) or "Không"
        prevs = ", ".join(subj.get("previous_subject_codes", [])) or "Không"
        parallels = ", ".join(subj.get("parallel_subject_codes", [])) or "Không"
        all_chunks.append({
            "chunk_id": f"{code}_prerequisites_info",
            "subject_code": code,
            "subject_name_vi": name_vi,
            "chunk_type": "prerequisites_info",
            "section_title": f"Điều kiện học phần môn {name_vi}",
            "content": (
                f"Điều kiện đăng ký học phần {name_vi} ({code}):\n"
                f"• Học phần tiên quyết: {prereqs}\n"
                f"• Học phần học trước: {prevs}\n"
                f"• Học phần song hành: {parallels}\n"
                f"• Loại học phần: {subj.get('course_type', 'Bắt buộc')} - Khối kiến thức: {subj.get('knowledge_block', 'Chuyên ngành')}"
            ),
            "metadata": {"subject_code": code}
        })

    # -------------------------------------------------------------
    # 2. TẠO CHUNKS TỪ KHUNG CHƯƠNG TRÌNH ĐÀO TẠO (PO / PLO)
    # -------------------------------------------------------------
    if frameworks:
        fw = frameworks[0]
        prog_name = fw.get("program_name", "Cử nhân Khoa học dữ liệu UTH")
        
        # Chunks Mục tiêu PO
        for po in fw.get("pos", []):
            all_chunks.append({
                "chunk_id": f"program_{po['po_id'].lower()}",
                "subject_code": "GENERAL_PROGRAM",
                "subject_name_vi": prog_name,
                "chunk_type": "program_objective",
                "section_title": f"Mục tiêu đào tạo - {po['po_id']}",
                "content": f"Mục tiêu đào tạo ngành {prog_name} ({po['po_id']}): {po['description']}",
                "metadata": {"po_id": po["po_id"]}
            })

        # Chunks Chuẩn đầu ra PLO & Performance Indicators (PIs)
        for plo in fw.get("plos", []):
            all_chunks.append({
                "chunk_id": f"program_{plo['plo_id'].lower()}",
                "subject_code": "GENERAL_PROGRAM",
                "subject_name_vi": prog_name,
                "chunk_type": "program_learning_outcome",
                "section_title": f"Chuẩn đầu ra ngành - {plo['plo_id']}",
                "content": f"Chuẩn đầu ra tốt nghiệp ngành {prog_name} ({plo['plo_id']}): {plo['description']}",
                "metadata": {"plo_id": plo["plo_id"]}
            })

        # Chunks Lộ trình theo Học kỳ (Semester 1 -> 8 Chunks)
        semesters = {
            "Học kỳ 1": ["001212 - Xác suất thống kê", "080101 - Phương pháp nghiên cứu", "122102 - Nhập môn KHDL", "124101 - Kỹ thuật lập trình", "125000 - Kiến trúc máy tính"],
            "Học kỳ 2": ["080102 - Quản trị học", "080103 - Tư duy thiết kế & Đổi mới sáng tạo", "121000 - Cơ sở dữ liệu", "122003 - Lập trình hướng đối tượng", "127100 - Phân tích dữ liệu định tính & định lượng"],
            "Học kỳ 3": ["005105 - Triết học Mác - Lênin", "122044 - Cấu trúc rời rạc", "124002 - Cấu trúc dữ liệu & Giải thuật", "124100 - Ngôn ngữ lập trình Python", "127102 - Các phương pháp Toán cho Máy học"],
            "Học kỳ 4": ["005106 - Kinh tế chính trị", "005004 - Pháp luật đại cương", "121002 - Thiết kế CSDL", "122105 - Công nghệ phần mềm", "123033 - An toàn thông tin", "124003 - Phân tích thiết kế giải thuật"],
            "Học kỳ 5": ["005107 - Chủ nghĩa xã hội khoa học", "121008 - Phân tích thiết kế hệ thống", "127123 - Lập trình Javascript/Typescript", "121137 - Quản trị doanh nghiệp CNTT", "127104 - Máy học"],
            "Học kỳ 6": ["005102 - Tư tưởng Hồ Chí Minh", "005108 - Lịch sử Đảng", "122041 - Khai thác dữ liệu", "127105 - Học sâu", "127106 - Trực quan hóa dữ liệu", "121003 - Hệ quản trị CSDL", "121031 - Lập trình Web", "127109 - Phân tích dữ liệu chuỗi thời gian & dự báo", "127111 - Xử lý âm thanh & NLP"],
            "Học kỳ 7": ["127107 - Đồ án thực tế KHDL", "121036 - Xử lý ảnh & Thị giác máy tính", "123039 - Điện toán đám mây", "127101 - Lập trình Blockchain & Smart Contract", "127108 - Học tăng cường", "127110 - Big Data & Ứng dụng", "127112 - Cấu trúc hệ thống Blockchain"],
            "Học kỳ 8": ["126003 - Học kỳ doanh nghiệp", "126000 - Thực tập tốt nghiệp", "126201 - Khóa luận tốt nghiệp", "127113 - Chuyên đề Thị giác máy tính", "127117 - Chuyên đề Chuỗi thời gian", "127118 - Chuyên đề Xử lý ngôn ngữ tự nhiên"]
        }
        for sem_name, course_list in semesters.items():
            all_chunks.append({
                "chunk_id": f"program_semester_{sem_name.lower().replace(' ', '_')}",
                "subject_code": "GENERAL_PROGRAM",
                "subject_name_vi": prog_name,
                "chunk_type": "semester_curriculum",
                "section_title": f"Lộ trình đào tạo {sem_name} ngành KHDL",
                "content": f"Danh mục các môn học được đề xuất học tại {sem_name} trong CTĐT Khoa học Dữ liệu (UTH):\n• " + "\n• ".join(course_list),
                "metadata": {"semester": sem_name}
            })

        # Chunks Khung trình độ quốc gia VQF (Kiến thức, Kỹ năng, Tự chủ)
        vqf_items = [
            ("KT1", "Kiến thức lý thuyết cốt lõi về toán, khoa học tự nhiên và nền tảng KHDL"),
            ("KT2", "Kiến thức chuyên sâu về phân tích dữ liệu, khai phá dữ liệu và trí tuệ nhân tạo"),
            ("KT3", "Kiến thức về quản lý hệ thống dữ liệu, bảo mật và đạo đức nghề nghiệp"),
            ("KN1", "Kỹ năng lập trình, sử dụng thành thạo các công cụ Python, R, SQL, Spark"),
            ("KN2", "Kỹ năng thiết kế, cài đặt và đánh giá mô hình học máy và học sâu"),
            ("KN3", "Kỹ năng trực quan hóa và thuyết trình phân tích kết quả dữ liệu"),
            ("KN4", "Kỹ năng làm việc nhóm, giao tiếp và ngoại ngữ chuyên ngành"),
            ("TCTN1", "Năng lực tự chủ trong nghiên cứu, cập nhật công nghệ mới"),
            ("TCTN2", "Trách nhiệm xã hội, tuân thủ pháp luật và đạo đức bảo vệ dữ liệu người dùng")
        ]
        for v_code, v_desc in vqf_items:
            all_chunks.append({
                "chunk_id": f"program_vqf_{v_code.lower()}",
                "subject_code": "GENERAL_PROGRAM",
                "subject_name_vi": prog_name,
                "chunk_type": "vqf_framework",
                "section_title": f"Khung trình độ quốc gia VQF - {v_code}",
                "content": f"Yêu cầu năng lực {v_code} theo Khung trình độ quốc gia Việt Nam (VQF) của Cử nhân Khoa học Dữ liệu UTH: {v_desc}",
                "metadata": {"vqf_code": v_code}
            })

        # Chunks Performance Indicators (PIs)
        pi_data = [
            ("PI2.1", "PLO2", "Giải quyết các bài toán kỹ thuật nhiều thông số ràng buộc đầu vào thuộc chuyên ngành KHDL bằng phương pháp cụ thể"),
            ("PI2.2", "PLO2", "Đánh giá các giải pháp khả thi và lựa chọn giải pháp tối ưu cho từng bài toán kỹ thuật chuyên ngành KHDL cụ thể"),
            ("PI2.3", "PLO2", "Phân tích bối cảnh nghề nghiệp trong các tổ chức quốc tế"),
            ("PI2.4", "PLO2", "Sử dụng tiếng Anh vào nghiên cứu tài liệu kỹ thuật ngành KHDL, đáp ứng trình độ năng lực tối thiểu bậc 3/6"),
            ("PI3.1", "PLO3", "Sử dụng công nghệ tiên tiến trong quản lý hoạt động chuyên môn"),
            ("PI3.2", "PLO3", "Xây dựng quy trình hoạt động nhóm có đặc tính hiệu quả, chuyên nghiệp, chủ động, công bằng"),
            ("PI3.4", "PLO3", "Lập kế hoạch xây dựng một dự án khởi nghiệp"),
            ("PI6.1", "PLO6", "Thiết kế sản phẩm theo yêu cầu cụ thể trong lĩnh vực KHDL"),
            ("PI6.2", "PLO6", "Đánh giá mức độ hiệu quả giải pháp khoa học dựa trên nguyên tắc pháp lý, đạo đức, và trách nhiệm nghề nghiệp"),
            ("PI6.3", "PLO6", "Xây dựng nội dung thuyết trình và bảo vệ quan điểm"),
            ("PI7.1", "PLO7", "Thảo luận chủ động đóng góp xây dựng nội dung bài học"),
            ("PI7.2", "PLO7", "Tham gia tích cực hoạt động nhóm theo hình thức được quy định")
        ]
        for pi_code, parent_plo, pi_desc in pi_data:
            all_chunks.append({
                "chunk_id": f"program_pi_{pi_code.lower().replace('.', '_')}",
                "subject_code": "GENERAL_PROGRAM",
                "subject_name_vi": prog_name,
                "chunk_type": "performance_indicator",
                "section_title": f"Chỉ báo thực hiện {pi_code} ({parent_plo})",
                "content": f"Chỉ báo thực hiện năng lực {pi_code} (thuộc Chuẩn đầu ra {parent_plo}) của ngành {prog_name}: {pi_desc}",
                "metadata": {"pi_code": pi_code, "parent_plo": parent_plo}
            })
        matrix = fw.get("course_contribution_plo_matrix", [])
        for m_idx, m in enumerate(matrix, 1):
            sc = m["subject_code"]
            sn = m.get("subject_name", "")
            plo = m["plo_id"]
            lvl = m["contribution_level"]
            all_chunks.append({
                "chunk_id": f"matrix_rel_{sc}_{plo.lower()}_{m_idx}",
                "subject_code": sc,
                "subject_name_vi": sn or f"Môn {sc}",
                "chunk_type": "course_plo_mapping",
                "section_title": f"Ánh xạ Chuẩn đầu ra {sc} -> {plo}",
                "content": f"Học phần {sn} ({sc}) đóng góp vào Chuẩn đầu ra ngành {plo} của CTĐT Khoa học Dữ liệu ở mức độ '{lvl}'.",
                "metadata": {"subject_code": sc, "plo_id": plo, "level": lvl}
            })

        # Chunks Ma trận đóng góp môn học gom nhóm
        subj_matrix = {}
        for m in matrix:
            sc = m["subject_code"]
            if sc not in subj_matrix:
                subj_matrix[sc] = []
            subj_matrix[sc].append(f"• Đóng góp vào {m['plo_id']} ở mức độ '{m['contribution_level']}'")

        for sc, rels in subj_matrix.items():
            all_chunks.append({
                "chunk_id": f"{sc}_plo_contribution_matrix",
                "subject_code": sc,
                "subject_name_vi": f"Môn học {sc}",
                "chunk_type": "plo_contribution_matrix",
                "section_title": f"Ma trận đóng góp Chuẩn đầu ra ngành (PLO)",
                "content": f"Mức độ đóng góp của học phần {sc} vào các chuẩn đầu ra ngành KHDL (PLOs):\n" + "\n".join(rels),
                "metadata": {"subject_code": sc}
            })

    # -------------------------------------------------------------
    # 3. TẠO CHUNKS TỪ DANH MỤC RUBRIC (A1.1 -> A5.5)
    # -------------------------------------------------------------
    for rub in rubrics:
        rub_code = rub.get("assessment_code", "")
        rub_name = rub.get("assessment_name", "")
        crit_list = []
        for c_idx, crit in enumerate(rub.get("criteria", []), 1):
            c_name = crit.get("criterion_name", "")
            lev = crit.get("levels", {})
            w = crit.get("weight", "")
            
            # Chunk tiêu chí chi tiết độc lập
            all_chunks.append({
                "chunk_id": f"rubric_{rub_code.lower().replace('.', '_')}_crit_{c_idx}",
                "subject_code": "GENERAL_RUBRIC",
                "subject_name_vi": f"Tiêu chí Rubric {rub_code}",
                "chunk_type": "rubric_criterion",
                "section_title": f"Tiêu chí {c_name} (Rubric {rub_code})",
                "content": (
                    f"Tiêu chí đánh giá '{c_name}' thuộc Rubric {rub_code} ({rub_name}) - Trọng số: {w}%:\n"
                    f"• Điểm A (8.5 - 10): {lev.get('A', '')}\n"
                    f"• Điểm B (7.0 - 8.4): {lev.get('B', '')}\n"
                    f"• Điểm C (5.5 - 6.9): {lev.get('C', '')}\n"
                    f"• Điểm D (4.0 - 5.4): {lev.get('D', '')}\n"
                    f"• Điểm F (0 - 3.9): {lev.get('F', '')}"
                ),
                "metadata": {"rubric_code": rub_code, "criterion": c_name}
            })

            crit_list.append(
                f"  - Tiêu chí: {c_name} (Trọng số {w}%):\n"
                f"    + Mức A (8.5-10): {lev.get('A', '')}\n"
                f"    + Mức B (7.0-8.4): {lev.get('B', '')}\n"
                f"    + Mức C (5.5-6.9): {lev.get('C', '')}\n"
                f"    + Mức D (4.0-5.4): {lev.get('D', '')}\n"
                f"    + Mức F (0-3.9): {lev.get('F', '')}"
            )

        # Chunk tổng quan cả bảng Rubric
        all_chunks.append({
            "chunk_id": f"rubric_{rub_code.lower().replace('.', '_')}",
            "subject_code": "GENERAL_RUBRIC",
            "subject_name_vi": f"Tiêu chí Rubric {rub_code}",
            "chunk_type": "rubric_detail",
            "section_title": f"Tiêu chuẩn đánh giá Rubric {rub_code} - {rub_name}",
            "content": f"Quy định chấm điểm theo Rubric {rub_code} ({rub_name}):\n" + "\n".join(crit_list),
            "metadata": {"rubric_code": rub_code}
        })

    # -------------------------------------------------------------
    # 4. GHI TẬP CHUNKS RA FILE CHUNK_SOURCES.JSON
    # -------------------------------------------------------------
    with open(CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"🎉 TỔNG KẾT: ĐÃ TẠO THÀNH CÔNG {len(all_chunks)} CHUNKS TRI THỨC NGUYÊN TỬ CHI TIẾT!")
    print(f"📁 Đường dẫn lưu: {CHUNKS_JSON_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    generate_all_deep_chunks()
