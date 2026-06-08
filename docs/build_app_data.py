"""
build_app_data.py — 将爬虫输出转换为选课规划助手可用格式
==========================================================
读取 uoft_programs_structured.json → 生成 enriched 后的 index.html

用法：
  python build_app_data.py

输入: docs/uoft_programs_structured.json
输出: src/index.html (用真实数据替换 CATALOG 和 PROGRAMS)
"""

import json
import re
import os
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)

# ─── 课程元数据自动生成规则 ──────────────────────────────────────────

# 课程代码 → 广度类别 (基于学科前缀的启发式规则)
SUBJECT_BREADTH = {
    # BR 1 — Creative & Cultural
    'ENG': 1, 'CIN': 1, 'DRM': 1, 'FA': 1, 'MUS': 1, 'ARC': 1,
    'VIS': 1, 'WRI': 1, 'CRE': 1, 'DHU': 1,
    # BR 2 — Thought, Belief & Behaviour
    'PHL': 5, 'REL': 5, 'HPS': 5,  # Ethics/Philosophy → BR5
    'PSY': 2, 'COG': 2, 'SOC': 2, 'POL': 2, 'HIS': 2, 'GGR': 2,
    'ANT': 2, 'ECO': 2, 'CRI': 2, 'IRE': 2, 'JPI': 2, 'JQR': 2,
    'SDS': 2, 'WGS': 2, 'CDN': 2, 'DTS': 2, 'PCJ': 2, 'FOR': 2,
    'SLA': 2, 'GER': 2, 'ITA': 2, 'SPA': 2, 'PRT': 2, 'EST': 2,
    'FIN': 2, 'HUN': 2, 'LAT': 2, 'MGR': 2, 'SAS': 2, 'NMC': 2,
    'CLA': 2, 'LIN': 2, 'JLP': 2, 'EAS': 2, 'CAS': 2, 'ABS': 2,
    'AFR': 2, 'CAR': 2, 'ERI': 2, 'JAL': 2, 'JFE': 2, 'JPE': 2,
    'KOR': 2, 'PLI': 2, 'PMS': 2, 'RLG': 2, 'SMC': 2, 'UNI': 2,
    'VIC': 2, 'NEW': 2, 'INN': 2, 'TRN': 2, 'WDW': 2,
    # BR 3 — Life Sciences & Environment
    'BIO': 3, 'CHM': 3, 'ENV': 3, 'IMM': 3, 'NRO': 3, 'MGY': 3,
    'HMB': 3, 'PSL': 3, 'CSB': 3, 'EEB': 3, 'BCB': 3, 'PCL': 3,
    'PHC': 3, 'LMP': 3, 'NFS': 3, 'ANA': 3, 'BCH': 3, 'LTE': 3,
    'FOR': 3, 'EHJ': 3, 'FCS': 3,
    # BR 4 — Mathematics & Physical Sciences
    'CSC': 4, 'MAT': 4, 'STA': 4, 'PHY': 4, 'AST': 4, 'APM': 4,
    'MSE': 4, 'JSC': 4, 'ECE': 4, 'BCB': 4,
    # BR 5 — Ethics, Philosophy & Thought
    'PHL': 5, 'HPS': 5, 'REL': 5, 'ETH': 5,
}

# 课程名称映射（常见课程 → 简短名称）
COURSE_NAME_MAP = {
    'CSC108H1': 'Introduction to Computer Programming',
    'CSC110Y1': 'Foundations of Computer Science I',
    'CSC111H1': 'Foundations of Computer Science II',
    'CSC148H1': 'Introduction to Computer Science',
    'CSC165H1': 'Mathematical Expression & Reasoning for CS',
    'CSC207H1': 'Software Design',
    'CSC209H1': 'Software Tools & Systems Programming',
    'CSC236H1': 'Introduction to Theory of Computation',
    'CSC240H1': 'Enriched Theory of Computation',
    'CSC258H1': 'Computer Organization',
    'CSC263H1': 'Data Structures & Analysis',
    'CSC265H1': 'Enriched Data Structures & Analysis',
    'CSC343H1': 'Introduction to Databases',
    'CSC301H1': 'Introduction to Software Engineering',
    'CSC309H1': 'Programming on the Web',
    'CSC311H1': 'Introduction to Machine Learning',
    'CSC316H1': 'Data Visualization',
    'CSC318H1': 'Design of Interactive Computational Media',
    'CSC320H1': 'Introduction to Visual Computing',
    'CSC324H1': 'Principles of Programming Languages',
    'CSC336H1': 'Numerical Methods',
    'CSC369H1': 'Operating Systems',
    'CSC373H1': 'Algorithm Design & Analysis',
    'CSC384H1': 'Introduction to Artificial Intelligence',
    'CSC401H1': 'Natural Language Computing',
    'CSC404H1': 'Introduction to Video Game Design',
    'CSC413H1': 'Neural Networks & Deep Learning',
    'CSC420H1': 'Introduction to Image Understanding',
    'CSC428H1': 'Human-Computer Interaction',
    'CSC454H1': 'The Business of Software',
    'CSC485H1': 'Computational Linguistics',
    'MAT137Y1': 'Calculus with Proofs',
    'MAT135H1': 'Calculus I',
    'MAT136H1': 'Calculus II',
    'MAT157Y1': 'Analysis I',
    'MAT223H1': 'Linear Algebra I',
    'MAT224H1': 'Linear Algebra II',
    'MAT235Y1': 'Multivariable Calculus',
    'MAT237Y1': 'Advanced Calculus',
    'MAT240H1': 'Enriched Linear Algebra I',
    'MAT247H1': 'Enriched Linear Algebra II',
    'STA130H1': 'Introduction to Statistical Reasoning',
    'STA237H1': 'Probability & Statistics I',
    'STA238H1': 'Probability & Statistics II',
    'STA247H1': 'Probability with CS Applications',
    'STA255H1': 'Statistical Theory',
    'STA257H1': 'Probability & Statistics I (Advanced)',
    'STA261H1': 'Probability & Statistics II (Advanced)',
    'STA302H1': 'Methods of Data Analysis I',
    'STA303H1': 'Methods of Data Analysis II',
    'STA304H1': 'Surveys & Sampling',
    'STA305H1': 'Experimental Design',
    'STA314H1': 'Statistical Methods for Machine Learning',
    'STA410H1': 'Statistical Computation',
    'STA414H1': 'Statistical Methods for Machine Learning II',
    'ECO101H1': 'Principles of Microeconomics',
    'ECO102H1': 'Principles of Macroeconomics',
    'ECO200H1': 'Microeconomic Theory I',
    'ECO202H1': 'Macroeconomic Theory I',
    'ECO220H1': 'Quantitative Methods in Economics',
    'BIO120H1': 'Adaptation and Biodiversity',
    'BIO130H1': 'Molecular and Cell Biology',
    'CHM135H1': 'Chemistry: Physical Principles',
    'CHM136H1': 'Introduction to Organic Chemistry',
    'PHY131H1': 'Introduction to Physics I',
    'PHY132H1': 'Introduction to Physics II',
    'PHY151H1': 'Foundations of Physics I',
    'PHY152H1': 'Foundations of Physics II',
    'PSY100H1': 'Introductory Psychology',
    'PSY201H1': 'Research Methods in Psychology',
    'PHL100Y1': 'Introduction to Philosophy',
    'LIN101H1': 'Introduction to Linguistics',
    'SOC100H1': 'Introduction to Sociology',
    'POL100H1': 'Introduction to Political Science',
    'HIS100H1': 'Introduction to History',
    'COG250Y1': 'Introduction to Cognitive Science',
    'ENV100H1': 'Introduction to Environmental Studies',
    'IMM250H1': 'Introduction to Immunology',
    'MGY200H1': 'Introduction to Molecular Genetics',
    'NRO100H1': 'Introduction to Neuroscience',
    'ENG100H1': 'Introduction to Literary Study',
}


def derive_fce(code):
    """从课程代码推导 FCE"""
    if re.search(r'Y[01]$', code):
        return 1.0
    # H courses are 0.5; H0 courses are usually 0.0 (no credit)
    if re.search(r'H0$', code):
        return 0.0
    return 0.5


def derive_breadth(code):
    """从学科前缀推导广度类别"""
    match = re.match(r'^([A-Z]{2,4})', code)
    if match:
        return SUBJECT_BREADTH.get(match.group(1), 4)  # 默认 BR4
    return 4


def derive_term(code):
    """推导推荐学期（启发式）"""
    if re.search(r'Y[01]$', code):
        return 'Y'  # 全年课程
    # H 课程：根据课程编号推断
    # 奇数字号通常为 Fall，偶数为 Winter（近似）
    num_match = re.search(r'(\d)HH?1$', code)
    if not num_match:
        num_match = re.search(r'(\d{3})H[01]$', code)
    if num_match:
        first_digit = int(num_match.group(1)[0]) if len(num_match.group(1)) >= 3 else int(num_match.group(1))
        return 'F' if first_digit % 2 == 1 else 'S'
    return 'F'  # 默认 Fall


def derive_name(code):
    """获取课程名称（映射表或生成占位名）"""
    if code in COURSE_NAME_MAP:
        return COURSE_NAME_MAP[code]
    subject = re.match(r'^([A-Z]{2,4})', code)
    subj_name = subject.group(1) if subject else 'Course'
    return f'{subj_name} Course'


def derive_desc(code):
    """生成课程描述占位"""
    return 'See UofT Academic Calendar for course description.'


# ─── 专业名称美化 ───────────────────────────────────────────────────

def beautify_program_name(name):
    """美化专业名称"""
    # 去掉冗余的 "(Science Program)", "(Arts Program)" 等
    name = re.sub(r'\s*\((?:Science|Arts)\s+Program\)', '', name, flags=re.IGNORECASE)
    # 多空格 → 单空格
    name = re.sub(r'\s+', ' ', name).strip()
    return name


# ─── 主函数 ──────────────────────────────────────────────────────────

def build(verbose=True, test_mode=False):
    # Read raw data (has completion_html for core/pool detection)
    raw_file = os.path.join(BASE_DIR, 'uoft_programs_raw.json')
    structured_file = os.path.join(BASE_DIR, 'uoft_programs_structured.json')
    html_file = os.path.join(PROJECT_DIR, 'src', 'index.html')
    output_file = html_file

    # 1. 读取爬虫数据
    if not os.path.exists(raw_file):
        print('[ERROR] Input file not found: ' + raw_file)
        print('  Please run: python scrape_uoft_programs.py --test')
        return False

    with open(raw_file, 'r', encoding='utf-8') as f:
        programs_raw = json.load(f)  # list of program dicts

    # Read structured data for courses and focus hierarchy
    courses_scraped = {}
    focus_hierarchy = {}
    if os.path.exists(structured_file):
        with open(structured_file, 'r', encoding='utf-8') as f:
            sdata = json.load(f)
            courses_scraped = sdata.get('courses', {})
            focus_hierarchy = sdata.get('focus_hierarchy', {})

    if verbose:
        print('Read %d programs, %d course codes' % (len(programs_raw), len(courses_scraped)))

    # 2. 过滤: 保留所有非 focus 类型 (specialist, major, minor, other)
    base_programs = [p for p in programs_raw if p['type'] in ('specialist', 'major', 'minor', 'other')]
    # Build focus lookup by lowercase code (to match focus_hierarchy keys)
    focus_programs = {}
    for p in programs_raw:
        if p.get('is_focus') or p['type'].startswith('focus'):
            focus_programs[p['code'].lower()] = p
            focus_programs[p['code'].upper()] = p  # both cases for robustness

    if test_mode:
        # 测试模式：仅保留 CS, DS, Math, Stats, Econ 相关专业
        test_subjects = ['Computer', 'Data', 'Math', 'Stat', 'Econ', 'Actuarial']
        base_programs = [p for p in base_programs if
            any(s.lower() in (p.get('name','') + p.get('section_name','')).lower() for s in test_subjects)]
        # 也过滤 focus hierarchy
        valid_ids = {p.get('id') or p['code'].lower() for p in base_programs}
        focus_hierarchy = {k: v for k, v in focus_hierarchy.items() if k in valid_ids}

    if verbose:
        print('Base programs: %d (after filtering)' % len(base_programs))
        print('Focus programs: %d' % len(focus_programs))
        print('Focus parents: %d' % len(focus_hierarchy))

    # 3. 加载 prerequisite 数据（如有）
    prereq_data = {}
    prereq_file = os.path.join(BASE_DIR, 'course_prereqs.json')
    if os.path.exists(prereq_file):
        with open(prereq_file, 'r', encoding='utf-8') as f:
            prereq_data = json.load(f)
        if verbose:
            print('Loaded prereq data for %d courses' % len(prereq_data))
    else:
        if verbose:
            print('No prereq data found (run scrape_course_prereqs.py first)')

    # 4. 构建课程目录 (仅收集被引用到的课程)
    used_courses = set()

    # ── UTSG campus filter ──
    def is_utsg(code):
        """Only keep St. George courses (H1/Y1/H0/Y0 suffix). Exclude UTM (H5/Y5) and UTSC (H3/Y3)."""
        return bool(re.search(r'[HY][01]$', code))

    # ── Pool course detection ──
    def split_core_pool(completion_html, is_focus=False):
        """Parse completion HTML to separate core required courses from elective pool courses."""
        if not completion_html:
            return set(), set()
        soup = BeautifulSoup(completion_html, 'html.parser')
        text = soup.get_text()

        # Different markers for base programs vs focus programs
        if is_focus:
            # Focus: only filter out "Suggested Related Courses"
            pool_markers = ['suggested related']
        else:
            pool_markers = [
                'selected from',
                'from the following list',
                'integrative, inquiry-based',
            ]
        split_pos = len(text)
        for marker in pool_markers:
            pos = text.lower().find(marker.lower())
            if pos >= 0 and pos < split_pos:
                split_pos = pos

        core_text = text[:split_pos]
        pool_text = text[split_pos:]

        core_codes = set(extract_course_codes_from_html_text(core_text))
        pool_codes = set(extract_course_codes_from_html_text(pool_text))
        return core_codes, pool_codes

    def extract_course_codes_from_html_text(html_or_text):
        """Extract course codes from HTML or plain text."""
        codes = set()
        # Try as HTML first
        soup = BeautifulSoup(html_or_text, 'html.parser')
        for a in soup.find_all('a', href=True):
            m = re.search(r'/course/([A-Z]{2,6}\d{3}[HY][0159])', a['href'], re.IGNORECASE)
            if m:
                codes.add(m.group(1).upper())
        # Also try plain text regex
        for m in re.finditer(r'([A-Z]{2,6}\d{3}[HY][0159])', html_or_text, re.IGNORECASE):
            codes.add(m.group(1).upper())
        return codes

    for prog in base_programs:
        for c in prog.get('course_codes', []):
            if is_utsg(c):
                used_courses.add(c)
    for fcode, fprog in focus_programs.items():
        for c in fprog.get('course_codes', []):
            if is_utsg(c):
                used_courses.add(c)

    # 限制课程数量（按被引用次数排序，取前 N 个高频课程）
    MAX_COURSES = 600
    popular = sorted(courses_scraped.items(), key=lambda x: len(x[1].get('programs', [])), reverse=True)
    for code, _ in popular:
        if len(used_courses) >= MAX_COURSES:
            break
        if is_utsg(code):
            used_courses.add(code)

    if verbose:
        print('Referenced courses: %d' % len(used_courses))

    # 为每个课程生成元数据
    catalog = {}
    for code in sorted(used_courses):
        entry = {
            'code': code,
            'name': derive_name(code),
            'desc': derive_desc(code),
            'fce': derive_fce(code),
            'breadth': derive_breadth(code),
            'term': derive_term(code),
        }
        # 合并 prereq 数据
        if code in prereq_data:
            pd = prereq_data[code]
            if pd.get('prereq'):
                entry['prereq'] = pd['prereq']
            if pd.get('breadth') and pd['breadth'] != entry['breadth']:
                # 使用官方的 breadth 编号（注意 UofT 的编号可能与我们的不同）
                # UofT: 1=Creative, 2=Thought, 3=Society, 4=Life, 5=Physical
                # 我们的: 1=Creative, 2=Social, 3=Life, 4=Math/Phys, 5=Ethics
                # 映射: UofT 5(Physical) → our 4, UofT 4(Life) → our 3, UofT 3(Society) → our 2, UofT 2(Thought) → our 5
                uoft_to_ours = {5: 4, 4: 3, 3: 2, 2: 5, 1: 1}
                entry['breadth'] = uoft_to_ours.get(pd['breadth'], entry['breadth'])
        catalog[code] = entry

    # 4. 转换 Program 格式
    programs_out = []
    for prog in base_programs:
        pid = prog.get('id') or prog['code'].lower()  # raw uses 'code', structured uses 'id'

        # 构建 focusOptions
        focus_options = []
        if pid in focus_hierarchy:
            for fcode in focus_hierarchy[pid]:
                # Case-insensitive lookup
                fprog = focus_programs.get(fcode) or focus_programs.get(fcode.upper()) or focus_programs.get(fcode.lower())
                if fprog:
                    focus_name = fprog.get('focus_name', fcode)
                    extra_courses = fprog.get('course_codes', [])
                    # Filter focus courses: UTSG only, core only, STEM subjects only
                    fcore_set, _ = split_core_pool(fprog.get('completion_html', ''), is_focus=True)
                    stem_prefixes = {'CSC','MAT','STA','ECE','BCB','JSC','LIN','MSE','PHY','CHM','BIO'}
                    extra_courses = [c for c in extra_courses
                        if is_utsg(c)
                        and (not fcore_set or c in fcore_set)
                        and c[:3] in stem_prefixes]
                    # 只用课程代码中不在父 program 中的课程
                    parent_courses = set(prog.get('course_codes', []))
                    extra_only = [c for c in extra_courses if c not in parent_courses]

                    focus_options.append({
                        'id': fcode.lower(),
                        'name': focus_name,
                        'extraCourses': extra_only,
                    })

        # 构建 requiredCourses — 仅包含核心必修课（排除选修池）
        year_groups = prog.get('year_groups', {})
        completion_html = prog.get('completion_html', '')
        all_codes = prog.get('course_codes', [])

        # Split into core vs pool using the helper function
        core_set = set()
        pool_set = set()
        if completion_html:
            core_set, pool_set = split_core_pool(completion_html)
        # Fallback: all courses are core
        if not core_set:
            core_set = set(all_codes)

        # UTSG filter
        core_set = {c for c in core_set if is_utsg(c)}

        # Filter year_groups to only include core UTSG courses
        required = {
            1: [c for c in year_groups.get('first_year', {}).get('courses', []) if c in core_set],
            2: [c for c in year_groups.get('second_year', {}).get('courses', []) if c in core_set],
            3: [c for c in year_groups.get('later_years', {}).get('courses', []) if c in core_set],
            4: [],
        }

        # If nothing filtered through, use all UTSG courses from year groups
        if not any(required.values()):
            required = {
                1: [c for c in year_groups.get('first_year', {}).get('courses', []) if is_utsg(c)],
                2: [c for c in year_groups.get('second_year', {}).get('courses', []) if is_utsg(c)],
                3: [c for c in year_groups.get('later_years', {}).get('courses', []) if is_utsg(c)],
                4: [],
            }
        if not any(required.values()):
            required[3] = [c for c in prog.get('course_codes', []) if is_utsg(c)]

        # Cap: any year with >6 courses → move overflow to pool
        MAX_PER_YEAR = 6
        for yr_key in [1, 2, 3]:
            if len(required[yr_key]) > MAX_PER_YEAR:
                overflow = required[yr_key][MAX_PER_YEAR:]
                required[yr_key] = required[yr_key][:MAX_PER_YEAR]
                pool_set.update(overflow)

        # prerequisites: 取大一课程的前几门
        prereqs = required.get(1, [])[:4] if required.get(1) else []

        # Pool courses: upper-year elective pool (UTSG-only)
        pool_list = sorted([c for c in pool_set if is_utsg(c)]) if pool_set else []

        programs_out.append({
            'id': pid,
            'name': beautify_program_name(prog.get('full_name', prog.get('name', ''))),
            'type': prog['type'],
            'focusOptions': focus_options,
            'prerequisites': prereqs,
            'requiredCourses': required,
            'poolCourses': pool_list,
            'totalFCE': prog.get('total_fce'),
        })

    if verbose:
        total_focus = sum(1 for p in programs_out if p['focusOptions'])
        print('Output programs: %d (with focus: %d)' % (len(programs_out), total_focus))
        print('Output courses: %d' % len(catalog))

    # 5. 生成 JS 代码
    catalog_js = _gen_catalog_js(catalog)
    programs_js = _gen_programs_js(programs_out)

    # 6. 替换 index.html 中的数据
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # 查找 CATALOG 的起止位置
    catalog_start = html.find('const CATALOG = {')
    catalog_end = html.find('};', catalog_start) + 2

    # 查找 PROGRAMS 的起止位置
    prog_marker = '// ─── PROGRAMS ─────────────────────────────────────────────────────'
    prog_comment_start = html.find(prog_marker)
    # PROGRAMS 数组结束位置
    programs_start = html.find('const PROGRAMS = [', prog_comment_start)
    programs_end = html.find('];', programs_start) + 2

    if catalog_start == -1 or programs_start == -1:
        print('[ERROR] 未在 index.html 中找到数据标记')
        return False

    # 替换
    html = (html[:catalog_start] +
            catalog_js +
            html[catalog_end:prog_comment_start] +
            programs_js +
            html[programs_end:])

    # 写回
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print('\n[DONE] Data written to: ' + output_file)
    print('  File size: %.0f KB' % (os.path.getsize(output_file) / 1024))
    return True


def _gen_catalog_js(catalog):
    """生成 CATALOG 常量 JS 代码"""
    lines = ['const CATALOG = {']
    for code in sorted(catalog.keys()):
        c = catalog[code]
        prereq_str = ''
        if c.get('prereq'):
            # Generate JS array of arrays: [["CSC148H1","CSC148H5"],["CSC165H1",...]]
            groups_js = '[' + ','.join(
                '[' + ','.join("'%s'" % _escape_js(alt) for alt in g) + ']'
                for g in c['prereq']
            ) + ']'
            prereq_str = ',prereq:' + groups_js
        lines.append(
            "  %s:{code:'%s',name:'%s',"
            "desc:'%s',fce:%s,breadth:%s,term:'%s'%s},"
            % (code, c['code'], _escape_js(c['name']),
               _escape_js(c['desc']), c['fce'], c['breadth'], c['term'], prereq_str)
        )
    lines.append('};')
    return '\n'.join(lines)


def _gen_programs_js(programs):
    """生成 PROGRAMS 常量 JS 代码"""
    lines = ['// ─── PROGRAMS ─────────────────────────────────────────────────────']
    lines.append('const PROGRAMS = [')

    for i, p in enumerate(programs):
        # focusOptions
        if p['focusOptions']:
            fo_lines = []
            for fo in p['focusOptions']:
                courses_str = ','.join(f"'{c}'" for c in fo['extraCourses'])
                fo_lines.append(
                    f"      {{id:'{fo['id']}',name:'{_escape_js(fo['name'])}',extraCourses:[{courses_str}]}},"
                )
            fo_block = '[\n' + '\n'.join(fo_lines) + '\n    ]'
        else:
            fo_block = '[]'

        # requiredCourses
        req = p['requiredCourses']
        req_parts = []
        for yr in [1, 2, 3, 4]:
            courses = req.get(yr, [])
            courses_str = ','.join(f"'{c}'" for c in courses)
            req_parts.append(f'{yr}:[{courses_str}]')
        req_str = '{' + ','.join(req_parts) + '}'

        # prerequisites
        prereq_str = ','.join(f"'{c}'" for c in p['prerequisites'])

        lines.append(
            f"  {{id:'{p['id']}',name:'{_escape_js(p['name'])}',type:'{p['type']}',"
            f"focusOptions:{fo_block},"
            f"prerequisites:[{prereq_str}],"
            f"requiredCourses:{req_str},"
            f"poolCourses:{json.dumps(p.get('poolCourses', []))},"
            f"{'totalFCE:' + str(p['totalFCE']) + ',' if p.get('totalFCE') else ''}"
            f"}},"
        )

    lines.append('];')
    return '\n'.join(lines)


def _escape_js(s):
    """转义 JS 字符串中的特殊字符"""
    if s is None:
        return ''
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ').replace('\r', '')


if __name__ == '__main__':
    import sys
    test_mode = '--test' in sys.argv
    build(test_mode=test_mode)
