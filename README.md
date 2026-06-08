# UofT Course Planner 🎓

A self-contained single-file web app for University of Toronto students to plan their degree path. Supports side-by-side comparison of 2–3 program combinations with real course data scraped from the [Arts & Science Academic Calendar](https://artsci.calendar.utoronto.ca/).

## Quick Start

1. Download [src/index.html](src/index.html)
2. Open it in any browser — no server, no install
3. Search your programs and start planning

## Features

- **357 programs** across all UofT Arts & Science departments (Specialist / Major / Minor)
- **4,700+ courses** with prerequisite chains and breadth categories
- **Side-by-side plan comparison** (up to 3 plans)
- **Difficulty path switching** — choose standard or enriched course paths
- **Drag & drop** courses between semesters
- **Summer overflow** — Fall/Winter > 6 courses auto-overflow to Summer
- **Prerequisite auto-inclusion** — adding a course auto-adds its prerequisites
- **Upper-Year Course Pool** — grouped by program with pathway descriptions
- **Program-aware filtering** — only shows valid course options for each program
- **Breadth requirement tracking** with progress bars
- **FCE cap warning** — alerts if mandatory courses exceed 20 FCE

## How It Works

- Data is scraped from the UofT Arts & Science Academic Calendar
- See [docs/information](docs/information) for details on the scraping process
- Run `python docs/scrape_uoft_programs.py` to refresh data
- Run `python docs/build_app_data.py` to rebuild index.html

## Tech

- Single HTML file, zero dependencies
- Vanilla HTML + CSS + JavaScript
- Works offline, mobile-responsive
