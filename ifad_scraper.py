#!/usr/bin/env python3
"""
IFAD Job Scraper
Scrapes job listings from International Fund for Agricultural Development and generates an RSS feed
"""

import time
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom

def setup_driver():
    """Set up Chrome WebDriver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_ifad_jobs():
    """Scrape job listings from IFAD"""
    url = "https://job.ifad.org/psc/IFHRPRDE/CAREERS/JOBS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL?Page=HRS_APP_SCHJOB_FL&Action=U"

    print(f"Starting scraper for: {url}")
    driver = setup_driver()
    jobs = []

    try:
        driver.get(url)
        print("Page loaded, waiting for JavaScript to render...")

        # Wait for PeopleSoft page to load
        wait = WebDriverWait(driver, 30)
        print("Waiting for job content to load...")
        time.sleep(20)  # PeopleSoft can be slow to render

        # Scroll to trigger any lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # Get page source
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Debug: Uncomment to save HTML for troubleshooting
        # with open('debug_ifad.html', 'w', encoding='utf-8') as f:
        #     f.write(page_source)
        # print("Debug: Saved page HTML to debug_ifad.html")

        # Try multiple strategies to find job listings
        job_elements = []

        # Strategy 1: Look for job ID elements (PeopleSoft pattern)
        job_id_elements = soup.find_all('span', attrs={'id': lambda x: x and 'HRS_APP_JBSCH_I_HRS_JOB_OPENING_ID$' in str(x)})
        if job_id_elements:
            print(f"Strategy 1 (PeopleSoft job IDs): Found {len(job_id_elements)} jobs")
            # Each job ID corresponds to a job - we'll extract full details
            for idx, id_elem in enumerate(job_id_elements):
                job_elements.append({'index': idx, 'id': id_elem.get_text(strip=True)})

        # Strategy 2: Look for job links if Strategy 1 failed
        if not job_elements:
            job_links = soup.find_all('a', attrs={'id': lambda x: x and 'SCH_JOB_TITLE$' in str(x)})
            if job_links:
                print(f"Strategy 2 (job title links): Found {len(job_links)} jobs")
                job_elements = job_links

        print(f"Processing {len(job_elements)} potential job listings...")

        for idx, element in enumerate(job_elements[:50]):  # Limit to first 50
            try:
                job_data = {}

                # Handle dict elements from Strategy 1
                if isinstance(element, dict):
                    job_idx = element['index']
                    job_data['job_id'] = element['id']

                    # Find corresponding title (it's a span, not a link)
                    title_elem = soup.find('span', attrs={'id': f'SCH_JOB_TITLE${job_idx}'})
                    if not title_elem or not title_elem.get_text(strip=True):
                        continue

                    job_data['title'] = title_elem.get_text(strip=True)
                    # Build job detail URL using job ID
                    job_data['link'] = f"https://job.ifad.org/psc/IFHRPRDE/CAREERS/JOBS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL?Page=HRS_APP_JBPST&Action=U&FOCUS=Applicant&SiteId=1&JobOpeningId={job_data['job_id']}"

                    # Find location
                    location_elem = soup.find('span', attrs={'id': f'LOCATION${job_idx}'})
                    job_data['location'] = location_elem.get_text(strip=True) if location_elem else "IFAD"

                    # Find department
                    dept_elem = soup.find('span', attrs={'id': f'HRS_APP_JBSCH_I_HRS_DEPT_DESCR${job_idx}'})
                    job_data['department'] = dept_elem.get_text(strip=True) if dept_elem else ""

                    # Create description
                    description_parts = [job_data['title']]
                    if job_data.get('location') and job_data['location'] != "IFAD":
                        description_parts.append(f"Location: {job_data['location']}")
                    if job_data.get('department'):
                        description_parts.append(f"Department: {job_data['department']}")
                    job_data['description'] = " | ".join(description_parts)

                    # Add job and continue to next
                    if job_data.get('title') and job_data.get('link'):
                        jobs.append(job_data)
                        print(f"  [OK] {job_data['title']}")
                    continue

                # Handle link elements from Strategy 2
                if hasattr(element, 'name') and element.name == 'a' and element.get('href'):
                    href = element['href']
                    if href.startswith('http'):
                        job_data['link'] = href
                    elif href.startswith('/'):
                        job_data['link'] = f"https://job.ifad.org{href}"
                    else:
                        job_data['link'] = f"https://job.ifad.org/psc/IFHRPRDE/CAREERS/JOBS/c/{href}"
                else:
                    link_elem = element.find('a', href=True)
                    if link_elem:
                        href = link_elem['href']
                        if href.startswith('http'):
                            job_data['link'] = href
                        elif href.startswith('/'):
                            job_data['link'] = f"https://job.ifad.org{href}"
                        else:
                            job_data['link'] = f"https://job.ifad.org/psc/IFHRPRDE/CAREERS/JOBS/c/{href}"
                    else:
                        # Try to find parent row and get link from there
                        parent = element.find_parent('tr')
                        if parent:
                            link_elem = parent.find('a', href=True)
                            if link_elem:
                                href = link_elem['href']
                                if href.startswith('http'):
                                    job_data['link'] = href
                                else:
                                    job_data['link'] = f"https://job.ifad.org{href}"

                        if not job_data.get('link'):
                            continue

                # Get job title
                if element.name == 'a':
                    job_data['title'] = element.get_text(strip=True)
                else:
                    # Look for title in span or div
                    title_elem = element.find(['span', 'div'], attrs={'id': lambda x: x and 'POSTING_TITLE' in str(x)})
                    if not title_elem:
                        title_elem = element.find(['h2', 'h3', 'h4', 'a'])

                    if title_elem:
                        job_data['title'] = title_elem.get_text(strip=True)
                    else:
                        job_data['title'] = element.get_text(strip=True)[:100]

                # Skip if title is too short or generic
                if not job_data.get('title') or len(job_data['title']) < 5:
                    continue

                skip_keywords = ['search', 'filter', 'login', 'sign in', 'home', 'about', 'all jobs']
                if any(keyword in job_data['title'].lower() for keyword in skip_keywords):
                    continue

                # Get location
                location_elem = element.find(['span', 'div'], attrs={'id': lambda x: x and 'LOCATION' in str(x)})
                if not location_elem:
                    location_elem = element.find(['span', 'div', 'p'], class_=lambda x: x and 'location' in str(x).lower())
                if not location_elem and element.name != 'a':
                    parent = element.find_parent('tr')
                    if parent:
                        location_elem = parent.find(['span', 'div'], attrs={'id': lambda x: x and 'LOCATION' in str(x)})

                job_data['location'] = location_elem.get_text(strip=True) if location_elem else "IFAD"

                # Get department/unit
                dept_elem = element.find(['span', 'div'], attrs={'id': lambda x: x and 'DEPARTMENT' in str(x)})
                job_data['department'] = dept_elem.get_text(strip=True) if dept_elem else ""

                # Create description
                description_parts = [job_data['title']]
                if job_data.get('location') and job_data['location'] != "IFAD":
                    description_parts.append(f"Location: {job_data['location']}")
                if job_data.get('department'):
                    description_parts.append(f"Department: {job_data['department']}")

                job_data['description'] = " | ".join(description_parts)

                if job_data['title'] and job_data['link']:
                    jobs.append(job_data)
                    print(f"  [OK] {job_data['title']}")

            except Exception as e:
                print(f"  [ERROR] Error processing element: {str(e)}")
                continue

        print(f"\nSuccessfully scraped {len(jobs)} jobs")

    except Exception as e:
        print(f"Error during scraping: {str(e)}")

    finally:
        driver.quit()

    return jobs

def generate_rss_feed(jobs, output_file='ifad_jobs.xml'):
    """Generate RSS 2.0 feed from job listings"""

    # Register atom namespace
    ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')

    # Create RSS root element
    rss = ET.Element('rss', version='2.0')

    # Create channel element
    channel = ET.SubElement(rss, 'channel')

    # Add channel metadata
    title = ET.SubElement(channel, 'title')
    title.text = 'IFAD Jobs'

    link = ET.SubElement(channel, 'link')
    link.text = 'https://job.ifad.org/psc/IFHRPRDE/CAREERS/JOBS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL?Page=HRS_APP_SCHJOB_FL&Action=U'

    description = ET.SubElement(channel, 'description')
    description.text = 'Job listings from International Fund for Agricultural Development (IFAD)'

    language = ET.SubElement(channel, 'language')
    language.text = 'en-us'

    # Add atom:link for self-reference
    atom_link = ET.SubElement(channel, '{http://www.w3.org/2005/Atom}link')
    atom_link.set('href', 'https://cinfoposte.github.io/ifad-jobs/ifad_jobs.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    # Add lastBuildDate
    last_build = ET.SubElement(channel, 'lastBuildDate')
    last_build.text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')

    # Add job items
    for job in jobs:
        item = ET.SubElement(channel, 'item')

        item_title = ET.SubElement(item, 'title')
        item_title.text = job.get('title', 'Untitled Position')

        item_link = ET.SubElement(item, 'link')
        item_link.text = job.get('link', '')

        item_description = ET.SubElement(item, 'description')
        item_description.text = job.get('description', '')

        # Add GUID
        guid = ET.SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = job.get('link', '')

    # Create pretty-printed XML
    xml_string = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_string)
    pretty_xml = dom.toprettyxml(indent='  ')

    # Remove extra blank lines
    pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(pretty_xml)

    print(f"\n[SUCCESS] RSS feed generated: {output_file}")
    print(f"  Total jobs in feed: {len(jobs)}")

def main():
    """Main execution function"""
    print("=" * 60)
    print("IFAD Job Scraper")
    print("=" * 60)

    # Scrape jobs
    jobs = scrape_ifad_jobs()

    if jobs:
        # Generate RSS feed
        generate_rss_feed(jobs)
        print("\n[SUCCESS] Scraping completed successfully!")
    else:
        print("\n[ERROR] No jobs found. Please check the website structure.")

    print("=" * 60)

if __name__ == "__main__":
    main()
