# UofT Course Planner 🎓

A self-contained single-file web app for University of Toronto students to plan their degree path. Compare 2–3 program combinations side-by-side, with real data from 357 programs and 4,700+ courses scraped from the Arts & Science Academic Calendar.

👉 **[Open the Planner](src/index.html)** — download and open in any browser.

## Features

- **357 programs** across all UofT Arts & Science departments (Specialist / Major / Minor)
- **4,700+ courses** with prerequisite chains and breadth categories
- **Side-by-side plan comparison** (up to 3 plans)
- **Difficulty path switching** — choose standard or enriched course paths (e.g. MAT137 ↔ MAT157)
- **Program-aware filtering** — only shows valid course options for each program's minimum requirements
- **Prerequisite auto-inclusion** — adding a course auto-adds its prerequisites
- **Drag & drop** courses between semesters
- **Summer overflow** — Fall/Winter > 6 courses auto-overflow to Summer
- **Upper-Year Course Pool** — grouped by program with topic-based pathways
- **Breadth requirement tracking** with progress bars
- **FCE cap warning** — alerts if mandatory courses exceed 20 FCE
- **Searchable program picker** — type to find any of the 357 programs
- **Mobile responsive** — works on phone and desktop

## Quick Start

1. Download [src/index.html](src/index.html)
2. Open it in any browser — no server, no install
3. Search your programs and start planning

## Development

Data is scraped from the [UofT Arts & Science Academic Calendar](https://artsci.calendar.utoronto.ca/):

```bash
pip install requests beautifulsoup4
python docs/scrape_uoft_programs.py    # Scrape all programs
python docs/scrape_course_prereqs.py   # Scrape prerequisites
python docs/build_app_data.py          # Rebuild index.html
```

## Tech

Single HTML file, zero dependencies. Vanilla HTML + CSS + JavaScript. Works offline.
