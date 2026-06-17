import argparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import time
import re
import csv
import random
import json
from typing import List, Dict, Any

# Helper to normalize text values

def clean_text(value: str) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()

# Job interface as per CSV columns
class Job:
    def __init__(self, kasb: str, ish_haqi: str, joylashuv: str, ish_turi: str, bandlik_turi: str, telefon: str, link: str):
        self.kasb = kasb
        self.ish_haqi = ish_haqi
        self.joylashuv = joylashuv
        self.ish_turi = ish_turi
        self.bandlik_turi = bandlik_turi
        self.telefon = telefon
        self.link = link

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Kasb": clean_text(self.kasb),
            "Ish haqi": clean_text(self.ish_haqi),
            "Joylashuv": clean_text(self.joylashuv),
            "Ish turi": clean_text(self.ish_turi),
            "Bandlik turi": clean_text(self.bandlik_turi),
            "Telefon": clean_text(self.telefon),
            "Link": clean_text(self.link)
        }

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

PHONE_REGEXES = [
    r"tel:\s*\+?[0-9\s\-()]{7,}",
    r"\+?998[\s\-()]*[0-9][0-9\s\-()]{6,}",
    r"\b0[0-9][0-9\s\-()]{7,}\b",
    r"\+?[0-9][0-9\s\-()]{8,14}[0-9]",
]


def create_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def normalize_phone(raw_phone: str) -> str:
    phone = raw_phone.strip()
    phone = re.sub(r"[^\d+()]", "", phone)
    if phone.count("+") > 1:
        phone = phone.replace("+", "")
    if phone.startswith("+"):
        digits = re.sub(r"[^\d]", "", phone[1:])
        phone = f"+{digits}" if digits else phone
    else:
        digits = re.sub(r"[^\d]", "", phone)
        phone = digits

    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) < 7 or len(digits) > 15:
        return ""
    return phone


def extract_phone_from_html(html: str) -> str:
    if not html:
        return "Ko'rsatilmadi"

    candidates = []
    for pattern in PHONE_REGEXES:
        for match in re.findall(pattern, html):
            phone = normalize_phone(match)
            if phone:
                candidates.append(phone)

    unique = []
    for phone in candidates:
        if phone not in unique:
            unique.append(phone)

    return unique[0] if unique else "Ko'rsatilmadi"


def fetch_phone_for_listing(session: requests.Session, link: str) -> str:
    try:
        response = session.get(link, timeout=15)
        response.raise_for_status()
        return extract_phone_from_html(response.text)
    except Exception as e:
        print(f"Error fetching phone from {link}: {e}")
        return "Ko'rsatilmadi"


def scrape_olx(max_pages: int = 100, target_jobs: int = 10000, fetch_phone: bool = True) -> List[Job]:
    jobs = []
    seen_links = set()
    session = create_session()
    page_errors = 0

    for page in range(1, max_pages + 1):
        url = f"https://www.olx.uz/d/rabota/?page={page}"
        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            page_errors += 1
            print(f"Error fetching OLX page {page}: {e}")
            if page_errors >= 3:
                print("Multiple page fetch failures, stopping early.")
                break
            time.sleep(5)
            continue

        page_errors = 0
        listings = soup.find_all('div', {'data-cy': 'l-card'})
        if not listings:
            listings = soup.select("div[data-cy='l-card'], li[data-cy='l-card'], article")
        if not listings:
            print(f"No listings found on page {page}. Stopping.")
            break

        print(f"Page {page}: found {len(listings)} listings, collected {len(jobs)} jobs so far")

        for listing in listings:
            if len(jobs) >= target_jobs:
                break

            try:
                link_tag = listing.find('a', href=True)
                title = link_tag.text.strip() if link_tag else ""
                link = link_tag['href'] if link_tag else ""
                if link and not link.startswith('http'):
                    link = f"https://www.olx.uz{link}"

                if not title or not link or '/list/user' in link or link in seen_links:
                    continue

                seen_links.add(link)

                salary_elem = listing.find('p', class_='css-3xwpr4')
                if salary_elem:
                    salary = salary_elem.text.strip()
                else:
                    text = listing.get_text(' ', strip=True)
                    salary_match = re.search(r"\d[\d\s,.]*\s*(?:сум|у\.е\.|у.е\.|usd|dollar|сум\b)", text, flags=re.IGNORECASE)
                    salary = salary_match.group(0).strip() if salary_match else "Noma'lum"

                info_tags = [tag.get_text(strip=True) for tag in listing.find_all('p', class_='css-1gwti7f')]
                joylashuv = info_tags[0] if len(info_tags) > 0 else "Noma'lum"
                ish_turi = info_tags[1] if len(info_tags) > 1 else ""
                bandlik_turi = info_tags[2] if len(info_tags) > 2 else ""
                telefon = fetch_phone_for_listing(session, link) if fetch_phone else "Ko'rsatilmadi"

                job = Job(
                    kasb=title,
                    ish_haqi=salary,
                    joylashuv=joylashuv,
                    ish_turi=ish_turi,
                    bandlik_turi=bandlik_turi,
                    telefon=telefon,
                    link=link
                )
                jobs.append(job)
            except Exception as e:
                print(f"Error parsing OLX job: {e}")

            time.sleep(0.5)

        if len(jobs) >= target_jobs:
            break

        time.sleep(1)

    return jobs

def scrape_hh() -> List[Job]:
    # HH scraping is not used in OLX-only mode.
    return []

def scrape_rabota() -> List[Job]:
    # Rabota.uz scraping is not used in OLX-only mode.
    return []

def main():
    parser = argparse.ArgumentParser(description="Scrape OLX job listings into CSV and JSON files.")
    parser.add_argument("--target", type=int, default=10000, help="Minimum number of job listings to collect.")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum OLX pages to scan.")
    parser.add_argument("--no-phone", action="store_true", help="Skip fetching phone numbers from detail pages.")
    args = parser.parse_args()

    all_jobs = []
    
    print(f"Scraping OLX (target={args.target} listings, max_pages={args.max_pages}, no_phone={args.no_phone})...")
    olx_jobs = scrape_olx(max_pages=args.max_pages, target_jobs=args.target, fetch_phone=not args.no_phone)
    all_jobs.extend(olx_jobs)
    time.sleep(2)  # Respectful delay
    
    # print("Scraping HH.uz...")
    # hh_jobs = scrape_hh()
    # all_jobs.extend(hh_jobs)
    # time.sleep(2)
    
    # Rabota.uz commented out due to domain resolution issues
    
    # Assign unique IDs if needed, but for CSV, not necessary
    for i, job in enumerate(all_jobs):
        pass  # No ID in CSV
    
    # Shuffle output so the CSV order changes each run
    random.shuffle(all_jobs)

    # Save to CSV in an Excel-friendly format and also save pretty JSON
    fieldnames = ["Kasb", "Ish haqi", "Joylashuv", "Ish turi", "Bandlik turi", "Telefon", "Link"]

    with open('scraped_jobs.csv', 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for job in all_jobs:
            writer.writerow(job.to_dict())

    with open('scraped_jobs.json', 'w', encoding='utf-8-sig') as f:
        json.dump([job.to_dict() for job in all_jobs], f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(all_jobs)} jobs and saved to scraped_jobs.csv and scraped_jobs.json")
    if len(all_jobs) < args.target:
        print(f"Warning: only {len(all_jobs)} jobs were found; the target was {args.target}.")

if __name__ == "__main__":
    main()