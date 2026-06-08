"""
多伦多大学本科生专业选课信息爬虫 (优化版)
==================================================
目标网站：https://artsci.calendar.utoronto.ca/

策略优化：
  - Section 页面的 accordion 内容已包含完整的 Enrolment + Completion Requirements
  - 因此只需爬 ~80 个 Section 页面即可获取所有专业的选课要求
  - 大大减少请求量（~80 个 vs ~1000+ 个 Program 详情页）
  - 对于关键 Program，可选择性深度抓取详情页

用法：
  python scrape_uoft_programs.py          # 完整爬取
  python scrape_uoft_programs.py --test   # 测试模式（仅抓 CS section）

输出：
  - uoft_programs_raw.json       # 所有专业原始数据
  - uoft_programs_structured.json # 结构化专业+课程数据
  - scrape_progress.json         # 断点续爬进度
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import os
import sys

# ============================================================================
# 配置
# ============================================================================
BASE_URL = "https://artsci.calendar.utoronto.ca"
REQUEST_TIMEOUT = 30
DELAY_BETWEEN_SECTIONS = 1.5
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_OUTPUT = os.path.join(OUTPUT_DIR, "uoft_programs_raw.json")
STRUCTURED_OUTPUT = os.path.join(OUTPUT_DIR, "uoft_programs_structured.json")
COURSES_OUTPUT = os.path.join(OUTPUT_DIR, "uoft_courses.json")
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "scrape_progress.json")

# 所有已知 Section URL（从 undergraduate programs 页面 + 手动验证收集）
KNOWN_SECTIONS = [
    "/section/Actuarial-Science",
    "/section/African-Studies",
    "/section/American-Studies",
    "/section/Anthropology",
    "/section/Archaeology",
    "/section/Art-History",
    "/section/ASIP",
    "/section/Astronomy-and-Astrophysics",
    "/section/Biochemistry",
    "/section/Biology",
    "/section/Cell-and-Systems-Biology",
    "/section/Centre-for-Caribbean-Studies",
    "/section/Centre-for-Jewish-Studies",
    "/section/Chemistry",
    "/section/Cinema-Studies-Institute",
    "/section/Classics",
    "/section/Cognitive-Science",
    "/section/Computer-Science",
    "/section/Contemporary-Asian-Studies",
    "/section/Criminology-and-Sociolegal-Studies",
    "/section/Data-Science",
    "/section/Diaspora-and-Transnational-Studies",
    "/section/Drama-Theatre-and-Performance-Studies",
    "/section/Earth-Sciences",
    "/section/East-Asian-Studies",
    "/section/Ecology-and-Evolutionary-Biology",
    "/section/Economics",
    "/section/English",
    "/section/Environment",
    "/section/European-Affairs",
    "/section/Forest-Conservation-and-Forest-Biomaterials-Science",
    "/section/French",
    "/section/Geography-and-Planning",
    "/section/German",
    "/section/History",
    "/section/History-and-Philosophy-of-Science-and-Technology",
    "/section/Human-Biology",
    "/section/Immunology",
    "/section/Indigenous-Studies",
    "/section/Industrial-Relations-and-Human-Resources",
    "/section/Innis-College",
    "/section/Italian",
    "/section/Laboratory-Medicine-and-Pathobiology",
    "/section/Latin-American-Studies",
    "/section/Linguistics",
    "/section/Materials-Science",
    "/section/Mathematics",
    "/section/Molecular-Genetics-and-Microbiology",
    "/section/Music",
    "/section/Near-and-Middle-Eastern-Civilizations",
    "/section/New-College",
    "/section/Nutritional-Sciences",
    "/section/Peace-Conflict-and-Justice",
    "/section/Pharmacology-and-Toxicology",
    "/section/Philosophy",
    "/section/Physics",
    "/section/Physiology",
    "/section/Planetary-Science",
    "/section/Political-Science",
    "/section/Portuguese",
    "/section/Psychology",
    "/section/Public-Policy",
    "/section/Religion",
    "/section/Rotman-Commerce",
    "/section/School-of-the-Environment",
    "/section/Sexual-Diversity-Studies",
    "/section/Slavic-and-East-European-Languages-and-Cultures",
    "/section/Sociology",
    "/section/South-Asian-Studies",
    "/section/Spanish",
    "/section/St-Michaels-College",
    "/section/Statistical-Sciences",
    "/section/Trinity-College",
    "/section/University-College",
    "/section/Victoria-College",
    "/section/Women-and-Gender-Studies",
    "/section/Woodsworth-College",
    "/section/Yiddish-Studies",
]

# 需要额外深度抓取的 Program 代码列表（常用于前置课程分析的）
DEEP_SCRAPE_CODES = [
    "ASSPE1689", "ASMAJ1689", "ASMIN1689",  # CS
    "ASSPE1687", "ASMIN0160",                 # DS
    "ASSPE1003",                               # Cell & Molecular Bio
    # 可根据需要扩展
]


# ============================================================================
# 工具函数
# ============================================================================

def safe_request(url, timeout=REQUEST_TIMEOUT):
    """发送 HTTP GET 请求"""
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        return resp
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] {url} — {e}")
        return None


def extract_course_codes(html_content):
    """
    从 HTML 内容中提取所有课程代码。
    匹配模式: /course/XXX000X0 格式的链接
    返回去重排序的代码列表。
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    codes = set()
    for a_tag in soup.find_all('a', href=True):
        m = re.search(r'/course/([A-Z]{2,6}\d{3}[HY][0159])', a_tag['href'], re.IGNORECASE)
        if m:
            codes.add(m.group(1).upper())
    return sorted(codes)


def extract_total_fce(text):
    """从文本中提取总学分要求。取所有匹配中数值最大的（总学分通常是最大值）。"""
    matches = re.findall(
        r'\((\d+\.?\d*)\s*(?:[-–]|to\s*)?(\d+\.?\d*)?\s*credits?',
        text, re.IGNORECASE
    )
    if not matches:
        return None
    best = 0
    for m in matches:
        val = float(m[1]) if m[1] else float(m[0])
        if val > best:
            best = val
    return best if best > 0 else None


def parse_year_sections(html_content):
    """
    从 Completion Requirements HTML 中按学年拆分课程。
    工作方式：在 HTML 中找到学年标记元素（如 <em>First year</em>），
    然后按这些标记将 HTML 切分为区块，每个区块内提取课程代码。

    返回: {
        "first_year": {"fce": float, "courses": [...]},
        "second_year": {"fce": float, "courses": [...]},
        "later_years": {"fce": float, "courses": [...]},
    }
    """
    if not html_content:
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}

    # 年份标记映射：HTML 文本匹配 → key
    year_markers = {
        'first year': 'first_year',
        'second year': 'second_year',
        'later years': 'later_years',
        'third year': 'later_years',
        'fourth year': 'later_years',
        'higher years': 'later_years',
    }

    # 找到所有可能的年份标记元素
    # 这些标记通常在 <em>, <strong>, <p> 标签内
    year_boundaries = []  # (key, element)
    all_elements = soup.find_all(['em', 'strong', 'p', 'h3', 'h4'])

    for elem in all_elements:
        text = elem.get_text(strip=True).lower()
        for marker, key in year_markers.items():
            if marker in text:
                # 检查是否是年份标题（如 "First year (2.5 credits):"）
                year_boundaries.append((key, elem))
                break

    # 如果没有找到年份标记，所有课程归入 later_years
    if not year_boundaries:
        all_courses = extract_course_codes(html_content)
        if all_courses:
            total_fce = extract_total_fce(soup.get_text())
            result["later_years"] = {"fce": total_fce, "courses": all_courses}
        return result

    # 去重并保持顺序
    seen = set()
    unique_boundaries = []
    for key, elem in year_boundaries:
        # 用元素在HTML中的位置去重
        elem_id = str(elem)[:100]
        if elem_id not in seen:
            seen.add(elem_id)
            unique_boundaries.append((key, elem))

    # 按文档顺序排序
    from bs4 import Tag
    doc_elems = list(soup.descendants)
    def find_index(elem):
        for i, d in enumerate(doc_elems):
            if d is elem:
                return i
        return -1

    unique_boundaries.sort(key=lambda x: find_index(x[1]))

    # 合并相邻同key的边界（third year和fourth year都归入later_years）
    merged = []
    for key, elem in unique_boundaries:
        if merged and merged[-1][0] == key:
            continue  # 跳过相邻同key
        merged.append((key, elem))

    # 获取整个容器的HTML用于切割
    container_html = str(soup)

    # 为每个年份区块提取课程
    for i, (key, elem) in enumerate(merged):
        # 确定下一个边界元素
        next_elem = merged[i + 1][1] if i + 1 < len(merged) else None

        # 获取此区块的HTML
        elem_html = str(elem)
        elem_start = container_html.find(elem_html[:80])  # 用前80字符定位
        if elem_start == -1:
            continue

        if next_elem:
            next_html = str(next_elem)[:80]
            next_start = container_html.find(next_html, elem_start + 1)
            if next_start == -1:
                section_html = container_html[elem_start:]
            else:
                section_html = container_html[elem_start:next_start]
        else:
            section_html = container_html[elem_start:]

        # 从HTML区块提取课程
        courses = extract_course_codes(section_html)
        soup_section = BeautifulSoup(section_html, 'html.parser')
        fce = extract_total_fce(soup_section.get_text())

        # 也尝试从标题行提取FCE
        if fce is None:
            header_text = elem.get_text(strip=True)
            m = re.search(r'(\d+\.?\d*)\s*credits?', header_text)
            if m:
                fce = float(m.group(1))

        if result.get(key):
            # 合并到已有条目
            result[key]["courses"] = sorted(set(result[key]["courses"] + courses))
            if result[key]["fce"] is None and fce is not None:
                result[key]["fce"] = fce
        else:
            result[key] = {"fce": fce, "courses": list(courses)}

    return result


def parse_program_entry(code, aria_label, content_row):
    """
    解析 Section 页面中的单个 Program 条目。

    参数:
        code: 程序代码（如 "ASSPE1689"）
        aria_label: aria-label 文本
        content_row: 包含 enrolment + completion 的 BeautifulSoup Tag

    返回: 结构化 dict
    """
    # --- 提取基础信息 ---
    info = {}
    info['code'] = code
    info['full_name'] = aria_label.strip()

    aria_lower = aria_label.lower()

    # 判断类型
    if aria_lower.startswith("focus in"):
        info['is_focus'] = True
        focus_m = re.search(r'Focus in (.+?)\s*\(', aria_label)
        info['focus_name'] = focus_m.group(1).strip() if focus_m else None

        # 提取父专业
        parent_m = re.search(r'\(([^)]+)\)\s*-\s*[A-Z]+\d+', aria_label)
        if parent_m:
            info['parent_name'] = parent_m.group(1).strip()

        if 'specialist' in aria_lower:
            info['type'] = 'focus_specialist'
        elif 'major' in aria_lower:
            info['type'] = 'focus_major'
        else:
            info['type'] = 'focus'
    elif 'specialist' in aria_lower:
        info['type'] = 'specialist'
        info['is_focus'] = False
        info['focus_name'] = None
    elif 'major' in aria_lower:
        info['type'] = 'major'
        info['is_focus'] = False
        info['focus_name'] = None
    elif 'minor' in aria_lower:
        info['type'] = 'minor'
        info['is_focus'] = False
        info['focus_name'] = None
    else:
        info['type'] = 'other'
        info['is_focus'] = False
        info['focus_name'] = None

    # 提取简短名称
    short_name = re.sub(r'\s*-\s*[A-Z]+\d+[A-Z]?\s*$', '', aria_label)
    short_name = re.sub(r'\s*\((?:Science|Arts|Specialist|Major|Minor)(?:\s+Program)?\)', '', short_name, flags=re.IGNORECASE)
    info['name'] = short_name.strip()

    # --- 提取 Enrolment Requirements ---
    enrolment_html = ""
    enrol_field = content_row.find('div', class_='views-field-field-enrolment-requirements')
    if enrol_field:
        fc = enrol_field.find('div', class_='field-content')
        if fc:
            enrolment_html = str(fc)

    # --- 提取 Completion Requirements ---
    completion_html = ""
    comp_field = content_row.find('div', class_='views-field-field-completion-requirements')
    if comp_field:
        fc = comp_field.find('div', class_='field-content')
        if fc:
            completion_html = str(fc)

    # --- 提取描述 ---
    description_html = ""
    body_field = content_row.find('div', class_='views-field-body')
    if body_field:
        fc = body_field.find('div', class_='field-content')
        if fc:
            description_html = str(fc)

    # --- 提取课程代码 ---
    all_courses = []
    all_courses.extend(extract_course_codes(completion_html))
    all_courses.extend(extract_course_codes(enrolment_html))
    all_courses = sorted(set(all_courses))

    # --- 提取总学分（优先从 completion，其次从 description） ---
    total_fce = None
    if completion_html:
        soup_text = BeautifulSoup(completion_html, 'html.parser').get_text()
        total_fce = extract_total_fce(soup_text)
    if total_fce is None and description_html:
        soup_text = BeautifulSoup(description_html, 'html.parser').get_text()
        total_fce = extract_total_fce(soup_text)

    # --- 提取学年分组 ---
    year_groups = {}
    if completion_html:
        year_groups = parse_year_sections(completion_html)

    # --- 检测是否有 "same requirements as" 的引用 ---
    is_same_req = False
    same_req_ref = None
    if completion_html:
        soup_text = BeautifulSoup(completion_html, 'html.parser').get_text()
        same_m = re.search(r'same set of requirements as.*?Focus in ([^.)]+)', soup_text, re.IGNORECASE)
        if same_m:
            is_same_req = True
            same_req_ref = same_m.group(1).strip()

    result = {
        **info,
        "total_fce": total_fce,
        "year_groups": year_groups,
        "course_codes": all_courses,
        "is_same_requirements": is_same_req,
        "same_requirements_ref": same_req_ref,
        "enrolment_html": enrolment_html,
        "completion_html": completion_html,
        "description_html": description_html,
    }
    return result


# ============================================================================
# 主流程
# ============================================================================

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed_sections": [], "all_programs": []}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def main():
    test_mode = '--test' in sys.argv

    print("\n" + "=" * 70)
    print("  多伦多大学本科生专业选课信息爬虫 v2")
    if test_mode:
        print("  [TEST MODE] 仅抓取 Computer Science section")
    print("=" * 70 + "\n")

    # --- 加载进度 ---
    progress = load_progress()
    completed_sections = set(progress.get("completed_sections", []))
    all_programs_list = progress.get("all_programs", [])

    # --- 确定要爬的 Section ---
    if test_mode:
        sections = ["/section/Computer-Science", "/section/Data-Science"]
    else:
        # 尝试动态发现，失败则用已知列表
        print("Phase 0: 发现 Section URL...")
        listing_url = f"{BASE_URL}/listing-program-subject-areas"
        resp = safe_request(listing_url)
        if resp:
            soup = BeautifulSoup(resp.text, 'html.parser')
            dynamic_sections = []
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith('/section/'):
                    dynamic_sections.append(href)
            if dynamic_sections:
                sections = list(dict.fromkeys(dynamic_sections))
                print(f"  Dynamic discovery: {len(sections)} sections found")
            else:
                sections = KNOWN_SECTIONS
                print(f"  Using known list: {len(sections)} sections")
        else:
            sections = KNOWN_SECTIONS
            print(f"  Using known list: {len(sections)} sections")

    pending_sections = [s for s in sections if s not in completed_sections]

    print(f"\n  Total sections: {len(sections)}")
    print(f"  Completed: {len(completed_sections)}")
    print(f"  Pending: {len(pending_sections)}")
    print()

    # --- Phase 1: 遍历 Section ---
    if pending_sections:
        print("=" * 60)
        print("Phase 1: Scraping section pages...")
        print("=" * 60)

    for i, section_url in enumerate(pending_sections, 1):
        section_name = section_url.replace('/section/', '')
        full_url = f"{BASE_URL}{section_url}"

        print(f"\n[{i}/{len(pending_sections)}] {section_name}")
        resp = safe_request(full_url)
        if not resp:
            completed_sections.add(section_url)
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        section_programs = []

        for heading in soup.find_all('h3', class_='js-views-accordion-group-header'):
            aria_div = heading.find('div', attrs={'aria-label': True})
            if not aria_div:
                continue

            code_m = re.search(r'-\s*([A-Z]+\d+[A-Z]?)\s*$', aria_div['aria-label'])
            if not code_m:
                continue

            code = code_m.group(1)
            content_row = heading.find_next('div', class_='views-row')

            if content_row:
                prog_data = parse_program_entry(code, aria_div['aria-label'], content_row)
                prog_data['section_name'] = section_name
                prog_data['section_url'] = section_url
                section_programs.append(prog_data)

        print(f"  -> {len(section_programs)} programs found")

        # 合并到全局列表（去重）
        existing_codes = {p['code'] for p in all_programs_list}
        for p in section_programs:
            if p['code'] not in existing_codes:
                all_programs_list.append(p)

        completed_sections.add(section_url)
        progress['completed_sections'] = list(completed_sections)
        progress['all_programs'] = all_programs_list
        save_progress(progress)

        if i < len(pending_sections):
            time.sleep(DELAY_BETWEEN_SECTIONS)

    print(f"\n--- Phase 1 Done: {len(all_programs_list)} total programs collected ---")

    # --- Phase 2: 选择性深度抓取 ---
    if not test_mode and DEEP_SCRAPE_CODES:
        print("\n" + "=" * 60)
        print("Phase 2: Deep-scraping key program pages...")
        print("=" * 60)

        all_programs_dict = {p['code']: p for p in all_programs_list}

        for i, code in enumerate(DEEP_SCRAPE_CODES, 1):
            if code in all_programs_dict and all_programs_dict[code].get('_deep_scraped'):
                print(f"  [{i}/{len(DEEP_SCRAPE_CODES)}] {code} - skipped (already done)")
                continue

            print(f"  [{i}/{len(DEEP_SCRAPE_CODES)}] {code}")
            url = f"{BASE_URL}/program/{code.lower()}"
            resp = safe_request(url)
            if not resp:
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')

            # 获取更干净的 completion requirements
            comp_div = soup.find('div', class_='field--name-field-completion-requirements')
            if comp_div:
                field_item = comp_div.find('div', class_='field__item')
                if field_item:
                    detail_completion = str(field_item)
                    # 更新课程列表
                    detail_courses = extract_course_codes(detail_completion)
                    detail_year = parse_year_sections(detail_completion)

                    if code in all_programs_dict:
                        all_programs_dict[code]['completion_html'] = detail_completion
                        all_programs_dict[code]['course_codes'] = sorted(set(
                            all_programs_dict[code].get('course_codes', []) + detail_courses
                        ))
                        all_programs_dict[code]['year_groups'] = detail_year
                        all_programs_dict[code]['_deep_scraped'] = True

            time.sleep(DELAY_BETWEEN_SECTIONS)

        all_programs_list = list(all_programs_dict.values())

    # --- 保存原始数据 ---
    print(f"\nSaving raw data to: {RAW_OUTPUT}")
    with open(RAW_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_programs_list, f, indent=2, ensure_ascii=False)

    # --- 清理进度 ---
    if not test_mode and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

    # --- 构建结构化数据 ---
    print("\n" + "=" * 60)
    print("Building structured data...")
    print("=" * 60)

    structured = build_structured(all_programs_list)

    with open(STRUCTURED_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {STRUCTURED_OUTPUT}")

    if not test_mode:
        # 保存课程索引
        with open(COURSES_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(structured.get('courses', {}), f, indent=2, ensure_ascii=False)
        print(f"  Saved: {COURSES_OUTPUT}")

    # --- 统计 ---
    print("\n" + "=" * 60)
    print("  SCRAPE COMPLETE - Summary")
    print("=" * 60)

    types_count = {}
    total_courses = set()
    for p in all_programs_list:
        t = p.get('type', 'unknown')
        types_count[t] = types_count.get(t, 0) + 1
        total_courses.update(p.get('course_codes', []))

    for t, c in sorted(types_count.items()):
        print(f"  {t:25s}: {c}")
    print(f"  {'Total programs':25s}: {len(all_programs_list)}")
    print(f"  {'Unique courses':25s}: {len(total_courses)}")
    print()


# ============================================================================
# 结构化输出
# ============================================================================

def build_structured(all_programs):
    """
    转换为选课规划助手兼容格式。

    输出:
    {
        "programs": [ { id, name, type, code, total_fce, focus_options, ... } ],
        "courses": { "CSC110Y1": { code, programs[], ... }, ... },
        "focus_hierarchy": { "ASSPE1689": ["ASFOC1689B", "ASFOC1689C", ...], ... }
    }
    """
    programs_out = []
    courses_map = {}  # course_code -> {code, programs[], ...}
    focus_map = {}    # parent_code -> [focus_code, ...]

    for p in all_programs:
        prog_id = p['code'].lower()

        prog_entry = {
            "id": prog_id,
            "name": p.get('name', ''),
            "full_name": p.get('full_name', ''),
            "type": p.get('type', 'unknown'),
            "code": p['code'],
            "total_fce": p.get('total_fce'),
            "is_focus": p.get('is_focus', False),
            "focus_name": p.get('focus_name'),
            "parent_name": p.get('parent_name'),
            "section_name": p.get('section_name', ''),
            "is_same_requirements": p.get('is_same_requirements', False),
            "same_requirements_ref": p.get('same_requirements_ref'),
            "course_codes": p.get('course_codes', []),
            "year_groups": p.get('year_groups', {}),
            "source_url": f"{BASE_URL}/program/{p['code'].lower()}",
        }

        programs_out.append(prog_entry)

        # 更新课程-专业映射
        for c_code in p.get('course_codes', []):
            if c_code not in courses_map:
                courses_map[c_code] = {
                    "code": c_code,
                    "programs": [],
                    "subject": c_code[:3],
                }
            courses_map[c_code]["programs"].append(prog_id)

        # Focus 层次映射：按已知的代码前缀 + 类型规则匹配
        if p.get('is_focus'):
            code = p['code']
            # 规则：ASFOC{base_code}{letter} — focus 代码基于父 program 代码变换
            # 例如 ASFOC1689B → parent 是 ASSPE1689 (specialist) 或 ASMAJ1689 (major)
            base_match = re.match(r'ASFOC(\d{4})([A-Z])', code)
            if base_match:
                base_num = base_match.group(1)  # e.g., "1689"
                focus_letter = base_match.group(2)  # e.g., "B"

                # 查找可能的父program：相同 base_num，但前缀是 ASSPE/ASMAJ/ASMIN
                parent_candidates = []
                for p2 in all_programs:
                    p2_code = p2['code']
                    if p2.get('is_focus'):
                        continue
                    # 检查基础数字是否匹配
                    if base_num in p2_code:
                        # Specialist 层级 focus (B,C,D,F,G,H,A,I,J,T → mostly specialist)
                        # Major 层级 focus (K,M,L,P,N,Q,O,R,S,U → mostly major)
                        specialist_letters = set('BCDFGHIAT')
                        major_letters = set('KLMNPQORSU')

                        if focus_letter in specialist_letters and p2['type'] == 'specialist':
                            parent_candidates.append((1, p2))  # 优先级1
                        elif focus_letter in major_letters and p2['type'] == 'major':
                            parent_candidates.append((1, p2))
                        elif p2['type'] in ('specialist', 'major'):
                            parent_candidates.append((2, p2))  # 优先级2（fallback）

                # 按优先级选择
                if parent_candidates:
                    parent_candidates.sort(key=lambda x: x[0])
                    parent_id = parent_candidates[0][1]['code'].lower()
                    if parent_id not in focus_map:
                        focus_map[parent_id] = []
                    focus_map[parent_id].append(prog_id)

    return {
        "programs": programs_out,
        "courses": courses_map,
        "focus_hierarchy": focus_map,
        "total_programs": len(programs_out),
        "total_courses": len(courses_map),
    }


if __name__ == "__main__":
    main()
