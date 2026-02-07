# IFAD Job Scraper

Automated RSS feed generator for job listings from the International Fund for Agricultural Development (IFAD).

## RSS Feed URL
**Live Feed:** `https://cinfoposte.github.io/ifad-jobs/ifad_jobs.xml`

## About
This scraper automatically fetches job listings from [IFAD Careers](https://job.ifad.org) and generates an RSS 2.0 compliant feed that updates twice weekly.

## Features
- ✅ Scrapes JavaScript-rendered job listings using Selenium
- ✅ Generates W3C-valid RSS 2.0 feed
- ✅ Automated updates via GitHub Actions (Sundays & Wednesdays at 9:00 UTC)
- ✅ Publicly accessible via GitHub Pages
- ✅ No server required - runs entirely on GitHub infrastructure

## Update Schedule
The feed automatically updates:
- **Sundays** at 9:00 UTC
- **Wednesdays** at 9:00 UTC

## Job Information Included
Each job listing includes:
- Job title
- Direct link to application page
- Location
- Department (when available)

## Technical Details
- **Language:** Python 3.11
- **Scraping:** Selenium WebDriver with Chrome headless
- **Parsing:** BeautifulSoup4
- **Format:** RSS 2.0
- **Platform:** PeopleSoft/Oracle HCM

## Local Usage

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser

### Installation
```bash
pip install -r requirements.txt
```

### Run Scraper
```bash
python ifad_scraper.py
```

This generates `ifad_jobs.xml` in the current directory.

## Validation
Validate the RSS feed at: https://validator.w3.org/feed/

## About IFAD
The International Fund for Agricultural Development (IFAD) is an international financial institution and specialized United Nations agency dedicated to eradicating poverty and hunger in rural areas of developing countries.

---

**Created by:** cinfoposte
**GitHub:** https://github.com/cinfoposte/ifad-jobs
**License:** MIT
