from loguru import logger
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib
from playwright.sync_api import sync_playwright

from job_recsys.data_models.job import Job


class EtsyJobScraper:
    def __init__(self, sitemap_url, output_dir="./data/etsy"):
        self.sitemap_url = sitemap_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.job_urls = []
        logger.info(f"EtsyJobScraper initialized with sitemap URL: {sitemap_url}")

    def hash_url(self, url):
        """Hashes a URL using SHA-256 and returns the hex digest."""
        hash_object = hashlib.sha256(url.encode("utf-8"))
        return hash_object.hexdigest()

    def fetch_sitemap(self):
        """Fetches and parses the sitemap XML to extract job URLs."""
        logger.info(f"Fetching the sitemap from {self.sitemap_url}")
        response = httpx.get(self.sitemap_url, headers=self.headers)

        if response.status_code not in [200, 202]:  # Accept 200 and 202 status codes
            logger.error(f"Failed to fetch the sitemap: HTTP {response.status_code}")
            return

        # Parse the XML sitemap with BeautifulSoup
        soup = BeautifulSoup(response.text, "xml")
        loc_elements = soup.find_all("loc")  # Find all <loc> tags

        # Filter only URLs for jobs
        self.job_urls = [
            loc.text.strip()
            for loc in loc_elements
            if loc.text.startswith("https://careers.etsy.com/jobs/")
        ]

        logger.info(f"Found {len(self.job_urls)} job URLs in the sitemap.")

    def fetch_with_playwright(self, job_url):
        """Fetches job details using Playwright to handle JavaScript rendering."""
        logger.info(f"Using Playwright to fetch job details for URL: {job_url}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(job_url, timeout=60000)  # Wait up to 60 seconds
                page.wait_for_load_state(
                    "networkidle"
                )  # Wait until no network activity
                content = page.content()  # Get the fully rendered HTML
                browser.close()
                return content
            except Exception as e:
                logger.error(f"Playwright failed for URL {job_url}: {e}")
                browser.close()
                return None

    def get_job_details(self, job_url):
        """Fetches job details from a given job URL."""
        logger.info(f"Fetching job details from URL: {job_url}")

        # Attempt to fetch using httpx first
        response = httpx.get(job_url, headers=self.headers)

        if response.status_code not in [200, 202]:
            logger.error(
                f"Failed to fetch job details with httpx: HTTP {response.status_code}"
            )
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        job_description = soup.find("div", class_="job-description")

        # If job_description is missing, fall back to Playwright
        if not job_description:
            logger.warning(
                f"Job description not found using httpx. Falling back to Playwright."
            )
            rendered_html = self.fetch_with_playwright(job_url)
            if not rendered_html:
                return None
            soup = BeautifulSoup(rendered_html, "html.parser")
            job_description = soup.find("div", class_="job-description")

        if job_description:
            details_text = job_description.get_text(separator="\n").strip()
            logger.debug(f"Successfully fetched job details: {details_text}")
            return {"description": details_text}
        else:
            logger.warning(f"Job description block not found for URL: {job_url}")
            return None

    def save_job(self, url, job_details):
        """Creates a Job object and saves it to a JSON file."""
        try:
            job = Job(url=url, job_description=job_details.get("description"))
            hashed_filename = self.hash_url(url) + ".json"
            file_path = self.output_dir / hashed_filename
            job.to_json(file_path)
        except Exception as e:
            logger.error(f"Failed to save job data for {url}: {e}")

    def get_all_job_details_with_storage(self):
        """Fetches job details from all job URLs and saves them as JSON files."""
        if not self.job_urls:
            logger.info("Job URL list is empty. Fetching from the sitemap.")
            self.fetch_sitemap()

        for job_url in self.job_urls:
            job_details = self.get_job_details(job_url)
            if job_details:
                self.save_job(job_url, job_details)


# Usage example
if __name__ == "__main__":
    sitemap_url = "https://careers.etsy.com/sitemap.xml"
    scraper = EtsyJobScraper(sitemap_url)

    # Fetch all job details and save them as JSON
    scraper.fetch_sitemap()
    scraper.get_all_job_details_with_storage()
