from loguru import logger
import httpx
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}


class JobScraper:
    """
    A class to scrape job descriptions from a job board API.

    It fetches the job board API response, extracts all job absolute URLs,
    and then retrieves the job description from each job page.
    """

    def __init__(self, board_api_url: str, headers: dict = None):
        """
        Initialize the JobScraper.

        Args:
            board_api_url (str): The URL to the job board API.
            headers (dict, optional): HTTP headers to use in requests.
                                      Defaults to a basic User-Agent header.
        """
        self.board_api_url = board_api_url
        self.headers = headers if headers is not None else DEFAULT_HEADERS
        logger.info(f"Initialized scraper with url {self.board_api_url}")

    def _fetch_jobs_data(self) -> dict:
        """
        Internal method to fetch the job board API JSON data.
        """
        response = httpx.get(self.board_api_url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        return data

    def get_job_urls(self) -> list:
        """
        Fetch the job board API and extract all absolute job URLs.

        Returns:
            list: A list of job URLs (strings).
        """
        data = self._fetch_jobs_data()
        urls = [
            job.get("absolute_url")
            for job in data.get("jobs", [])
            if job.get("absolute_url")
        ]
        logger.info(f"Found {len(urls)} urls")
        return urls

    def scrape_job_description(self, job_url: str) -> str:
        """
        Given a job URL, fetch the page and extract the job description text.

        Args:
            job_url (str): The URL of the job posting.

        Returns:
            str: The job description extracted from the HTML content.
        """
        logger.info("Scraping job description")
        response = httpx.get(job_url, headers=self.headers, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        job_description = "\n".join(paragraphs)
        return job_description

    def get_job_descriptions(self, limit: int = 1) -> list:
        """
        Fetch job descriptions for the first `limit` job URLs from the board API.

        Args:
            limit (int): The maximum number of job descriptions to fetch.

        Returns:
            list: A list of tuples, each containing (job_url, job_description).
        """
        job_urls = self.get_job_urls()
        selected_urls = job_urls[:limit]
        descriptions = []

        for url in selected_urls:
            try:
                description = self.scrape_job_description(url)
                descriptions.append((url, description))
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")

        logger.info(f"Extracted {len(descriptions)} descriptions")
        return descriptions

    def get_unique_metadata_values(self) -> set:
        """
        Extract all unique metadata 'value's from the job board API response.

        Returns:
            set: A set of unique metadata values.
        """
        data = self._fetch_jobs_data()
        unique_metadata = set()
        for job in data.get("jobs", []):
            for meta in job.get("metadata", []):
                value = meta.get("value")
                if value:
                    unique_metadata.add(value)
        logger.info(f"Extracted {len(unique_metadata)} unique metadata values")
        return unique_metadata

    def get_unique_department_values(self) -> set:
        """
        Extract all unique department values from the job board API response.
        These values are the full department strings provided by the API.

        Returns:
            set: A set of unique department strings.
        """
        data = self._fetch_jobs_data()
        unique_departments = set()
        for job in data.get("jobs", []):
            for dept in job.get("departments", []):
                name = dept.get("name")
                if name:
                    unique_departments.add(name)
        logger.info(f"Extracted {len(unique_departments)} unique department values")
        return unique_departments

    def get_jobs_by_department(self, department_prefix: str = "ENG") -> list:
        """
        Returns a list of job objects from the API where at least one department's name starts with the given prefix.

        Args:
            department_prefix (str): The prefix to filter department names by (default is "ENG").

        Returns:
            list: A list of job objects that belong to the specified department.
        """
        data = self._fetch_jobs_data()
        matching_jobs = []
        for job in data.get("jobs", []):
            for dept in job.get("departments", []):
                name = dept.get("name", "")
                if name.startswith(department_prefix):
                    matching_jobs.append(job)
                    break
        logger.info(
            f"Found {len(matching_jobs)} jobs with department prefix '{department_prefix}'"
        )
        return matching_jobs

    def get_unique_department_prefixes(self) -> set:
        """
        Extracts and returns all unique department prefixes from the job board API response.
        A department prefix is assumed to be the first segment of the department name, split by " : ".

        Returns:
            set: A set of unique department prefixes.
        """
        data = self._fetch_jobs_data()
        prefixes = set()
        for job in data.get("jobs", []):
            for dept in job.get("departments", []):
                name = dept.get("name", "")
                if name:
                    prefix = name.split(" : ")[0].strip()
                    prefixes.add(prefix)
        logger.info(f"Extracted {len(prefixes)} unique department prefixes")
        return prefixes


if __name__ == "__main__":
    board_api_url = (
        "https://boards-api.greenhouse.io/v1/boards/andurilindustries/jobs?content=true"
    )
    scraper = JobScraper(board_api_url)

    department_prefixes = scraper.get_unique_department_prefixes()
    print("Unique Department Prefixes:")
    for prefix in department_prefixes:
        print(f"- {prefix}")

    # Example: Get all jobs in the ENG department
    eng_jobs = scraper.get_jobs_by_department("ENG")
    print("Jobs in the ENG department:")
    for job in eng_jobs:
        print(
            f"- {job.get('title')} at {job.get('company_name')}\n{job.get('absolute_url')}"
        )
