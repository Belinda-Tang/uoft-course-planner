"""
scrape_course_prereqs.py — Scrape prerequisite data from course detail pages
=============================================================================
Reads all course codes from index.html CATALOG, fetches each course page,
extracts prerequisite/exclusion/breadth info.

Usage:
  python scrape_course_prereqs.py

Output: docs/course_prereqs.json
  { "CSC236H1": {"prereq_groups": [...], "exclusions": [...], "breadth_num": 5}, ... }
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time

BASE_URL = "https://artsci.calendar.utoronto.ca"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "course_prereqs.json")
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prereq_progress.json")
HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "index.html")
DELAY = 0.5  # seconds between requests


def extract_course_codes_from_html():
    """Extract all course codes from index.html CATALOG."""
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()
    m = re.search(r'const CATALOG = \{(.+?)\};', html, re.DOTALL)
    if not m:
        return []
    return sorted(set(re.findall(r"'([A-Z]{2,6}\d{3}[HY][0159])'", m.group(1))))


def scrape_course_page(code):
    """Scrape prerequisite data from a course detail page."""
    url = "%s/course/%s" % (BASE_URL, code)
    try:
        resp = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
    except Exception as e:
        print("  [FAIL] %s: %s" % (code, e))
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    # --- Prerequisites ---
    prereq_div = soup.find('div', class_='field--name-field-prerequisite')
    prereq_text = ""
    prereq_codes = []
    prereq_groups = []  # [[group1_alternatives], [group2_alternatives], ...]

    if prereq_div:
        field_item = prereq_div.find('div', class_='field__item')
        if field_item:
            prereq_text = field_item.get_text(strip=True)
            # Extract course codes from prerequisite field
            for a in field_item.find_all('a', href=True):
                m = re.search(r'/course/([A-Z]{2,6}\d{3}[HY][0159])', a['href'], re.IGNORECASE)
                if m:
                    prereq_codes.append(m.group(1).upper())

            # Parse AND/OR structure
            # ";" separates AND groups, "/" separates OR alternatives
            html_str = str(field_item)
            # Split by ";" to get AND groups
            and_parts = re.split(r';\s*(?=<|60%|70%|77%|80%)', html_str)
            # Alternative: just split by "; " and check each part
            and_parts = html_str.split(';')
            for part in and_parts:
                group_codes = []
                for a in BeautifulSoup(part, 'html.parser').find_all('a', href=True):
                    m = re.search(r'/course/([A-Z]{2,6}\d{3}[HY][0159])', a['href'], re.IGNORECASE)
                    if m:
                        group_codes.append(m.group(1).upper())
                if group_codes:
                    prereq_groups.append(group_codes)

    # --- Exclusions ---
    excl_div = soup.find('div', class_='field--name-field-exclusion')
    exclusion_codes = []
    if excl_div:
        field_item = excl_div.find('div', class_='field__item')
        if field_item:
            for a in field_item.find_all('a', href=True):
                m = re.search(r'/course/([A-Z]{2,6}\d{3}[HY][0159])', a['href'], re.IGNORECASE)
                if m:
                    exclusion_codes.append(m.group(1).upper())

    # --- Breadth ---
    breadth_div = soup.find('div', class_='field--name-field-breadth-requirements')
    breadth_num = None
    if breadth_div:
        items = breadth_div.find_all('div', class_='field__item')
        for item in items:
            text = item.get_text(strip=True)
            # "The Physical and Mathematical Universes (5)"
            m = re.search(r'\((\d)\)', text)
            if m:
                breadth_num = int(m.group(1))
                break

    return {
        "code": code,
        "prereq_text": prereq_text,
        "prereq_groups": prereq_groups,
        "exclusions": exclusion_codes,
        "breadth_num": breadth_num,
    }


def main():
    codes = extract_course_codes_from_html()
    print("Found %d courses in CATALOG" % len(codes))

    # Load progress
    progress = {}
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)

    results = progress.get('results', {})
    completed = set(results.keys())

    pending = [c for c in codes if c not in completed]
    print("Already done: %d, pending: %d" % (len(completed), len(pending)))

    batch_size = 50
    for i, code in enumerate(pending):
        if i % batch_size == 0:
            print("  [%d/%d] ..." % (i+1, len(pending)))

        result = scrape_course_page(code)
        if result:
            results[code] = result

        # Save progress every 50
        if (i+1) % batch_size == 0:
            progress['results'] = results
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
            # Also save partial output
            save_simple(results)
            print("  [%d/%d] saved progress" % (i+1, len(pending)))

        time.sleep(DELAY)

    # Final save
    progress['results'] = results
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)

    save_simple(results)

    # Stats
    with_prereqs = sum(1 for r in results.values() if r and r.get('prereq_groups'))
    with_breadth = sum(1 for r in results.values() if r and r.get('breadth_num'))
    print("\nDone! %d courses scraped" % len(results))
    print("  With prerequisites: %d" % with_prereqs)
    print("  With breadth info: %d" % with_breadth)


def save_simple(results):
    """Save a simplified version for the app."""
    simple = {}
    for code, data in results.items():
        if not data:
            continue
        entry = {}
        if data.get('prereq_groups'):
            entry['prereq'] = data['prereq_groups']
        if data.get('exclusions'):
            entry['excl'] = data['exclusions']
        if data.get('breadth_num'):
            entry['breadth'] = data['breadth_num']
        if entry:
            simple[code] = entry
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(simple, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
