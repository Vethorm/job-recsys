from loguru import logger
import httpx
from bs4 import BeautifulSoup
from pathlib import Path
import hashlib

from job_recsys.data_models.job import Job


class AirbnbJobScraper:
    def __init__(self, sitemap_url, output_dir="./data/airbnb"):
        self.sitemap_url = sitemap_url
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True, exist_ok=True
        )  # Ensure the output directory exists
        self.job_urls = []
        logger.info(
            f"JobScraper initialized with sitemap URL: {sitemap_url} and output directory: {self.output_dir}"
        )

    def hash_url(self, url):
        """Hashes a URL using SHA-256 and returns the hex digest."""
        hash_object = hashlib.sha256(url.encode("utf-8"))
        return hash_object.hexdigest()

    def fetch_sitemap(self):
        """Fetches and parses the sitemap XML to extract job URLs."""
        logger.info(f"Fetching the sitemap from {self.sitemap_url}")
        response = httpx.get(self.sitemap_url, headers=self.headers)

        if response.status_code != 200:
            logger.error(f"Failed to fetch the sitemap: HTTP {response.status_code}")
            return

        # Parse the XML sitemap with BeautifulSoup
        soup = BeautifulSoup(response.text, "xml")
        loc_elements = soup.find_all("loc")  # Find all <loc> tags

        self.job_urls = [
            loc.text.strip()
            for loc in loc_elements
            if loc.text.startswith("https://careers.airbnb.com/positions/")
        ]

        logger.info(f"Found {len(self.job_urls)} job URLs in the sitemap.")

    def get_job_details(self, job_url):
        """Fetches job details from a given job URL."""
        logger.info(f"Fetching job details from URL: {job_url}")
        response = httpx.get(job_url, headers=self.headers)

        if response.status_code != 200:
            logger.error(
                f"Failed to fetch job details from {job_url}: HTTP {response.status_code}"
            )
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        job_content = soup.find("div", class_="job-detail active")

        if job_content:
            logger.debug(f"Successfully fetched job details from {job_url}")
            return job_content.text.strip()
        else:
            logger.warning(f"Job content not found for {job_url}")
            return None

    def save_job(self, url, job_description):
        """Creates a Job object and saves it to a JSON file."""
        try:
            job = Job(url=url, job_description=job_description)
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
            job_description = self.get_job_details(job_url)
            if job_description:
                self.save_job(job_url, job_description)


# Usage example
if __name__ == "__main__":
    sitemap_url = "https://careers.airbnb.com/positions-sitemap.xml"
    scraper = AirbnbJobScraper(sitemap_url)

    # Fetch all job details and save them as JSON
    scraper.fetch_sitemap()
    scraper.get_all_job_details_with_storage()
