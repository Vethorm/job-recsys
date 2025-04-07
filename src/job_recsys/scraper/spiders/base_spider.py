"""Base spider implementation for scraping job listings."""

from abc import ABC, abstractmethod
from collections.abc import Generator

import scrapy
from loguru import logger

from job_recsys.core.models.job import JobData, JobListing
from job_recsys.data.job_storage import JobStorage


class BaseJobSpider(scrapy.Spider, ABC):
    """Base spider for scraping job listings with storage integration.

    Provides common functionality for job listing spiders including:
    - Integration with JobStorage for persistence
    - URL deduplication based on existing records
    - Abstract methods for site-specific implementations

    Attributes:
        company (str): The company name these job listings belong to
        job_storage (JobStorage): Storage instance for persisting job listings
        start_urls (list): Initial URLs to start crawling from
    """

    name = "base_job_spider"  # Will be overridden by subclasses

    def __init__(self, company: str, job_storage: JobStorage, *args, **kwargs):
        """Initialize the base job spider.

        Args:
            company: Name of the company whose jobs are being scraped
            job_storage: Storage instance for saving job listings
            *args: Additional positional arguments passed to parent constructor
            **kwargs: Additional keyword arguments passed to parent constructor
        """
        super().__init__(*args, **kwargs)
        self.company = company
        self.job_storage = job_storage

        self.start_urls = kwargs.get("start_urls", [])

    def parse(self, response: scrapy.http.Response) -> Generator:
        """Default parse method that handles sitemap or listing page response.

        Delegates to appropriate parsing method based on response type.

        Args:
            response: The HTTP response to parse

        Yields:
            Requests for job detail pages or parsed job listings
        """
        if self._is_sitemap(response):
            yield from self.parse_sitemap(response)
        elif self._is_job_listing_page(response):
            yield from self.parse_listing_page(response)
        else:
            yield from self.parse_job_detail(response)

    def parse_sitemap(self, response: scrapy.http.Response) -> Generator:
        """Parse sitemap XML to extract job listing URLs.

        Args:
            response: The HTTP response containing the sitemap

        Yields:
            Requests to job detail pages
        """
        job_urls = self._extract_job_urls_from_sitemap(response)

        filtered_urls = self._filter_existing_urls(job_urls)

        for url in filtered_urls:
            yield scrapy.Request(url=url, callback=self.parse_job_detail)

    def parse_listing_page(self, response: scrapy.http.Response) -> Generator:
        """Parse a page containing multiple job listings.

        Args:
            response: The HTTP response containing job listings

        Yields:
            Requests to job detail pages or next listing pages
        """
        job_urls = self._extract_job_urls_from_listing(response)

        filtered_urls = self._filter_existing_urls(job_urls)

        for url in filtered_urls:
            yield scrapy.Request(url=url, callback=self.parse_job_detail)

        next_page = self._get_next_page_url(response)
        if next_page:
            yield scrapy.Request(url=next_page, callback=self.parse_listing_page)

    def parse_job_detail(self, response: scrapy.http.Response) -> Generator:
        """Parse a job detail page to extract job information.

        Args:
            response: The HTTP response containing job details

        Yields:
            Item or dictionary containing the parsed job data
        """
        job_title = self._extract_job_title(response)
        job_location = self._extract_job_location(response)
        job_description = self._extract_job_description(response)

        job_data = JobData(title=job_title, location=job_location, description=job_description, raw_html=response.text)

        job_listing = JobListing.create(url=response.url, company=self.company, job_data=job_data)

        try:
            storage_key = self.job_storage.store_job(job_listing)
            logger.info(f"Stored job listing: {job_listing} at key {storage_key}")
            yield {"status": "success", "job": job_listing.model_dump()}
        except Exception as e:
            logger.error(f"Error storing job listing {response.url}: {e!s}")
            yield {"status": "error", "url": response.url, "error": str(e)}

    def _filter_existing_urls(self, urls: list[str]) -> list[str]:
        """Filter out URLs that already exist in storage.

        Args:
            urls: List of job listing URLs to filter

        Returns:
            List of URLs that don't exist in storage yet
        """
        return [url for url in urls if not self.job_storage.job_exists(self.company, url)]

    @abstractmethod
    def _is_sitemap(self, response: scrapy.http.Response) -> bool:
        """Determine if the response is a sitemap.

        Args:
            response: The HTTP response to check

        Returns:
            True if the response is a sitemap, False otherwise
        """
        pass

    @abstractmethod
    def _is_job_listing_page(self, response: scrapy.http.Response) -> bool:
        """Determine if the response is a job listing page with multiple jobs.

        Args:
            response: The HTTP response to check

        Returns:
            True if the response is a job listing page, False otherwise
        """
        pass

    @abstractmethod
    def _extract_job_urls_from_sitemap(self, response: scrapy.http.Response) -> list[str]:
        """Extract job detail URLs from a sitemap.

        Args:
            response: The HTTP response containing the sitemap

        Returns:
            List of job detail URLs
        """
        pass

    @abstractmethod
    def _extract_job_urls_from_listing(self, response: scrapy.http.Response) -> list[str]:
        """Extract job detail URLs from a listing page.

        Args:
            response: The HTTP response containing job listings

        Returns:
            List of job detail URLs
        """
        pass

    @abstractmethod
    def _get_next_page_url(self, response: scrapy.http.Response) -> str | None:
        """Get the URL of the next page of job listings, if any.

        Args:
            response: The HTTP response of the current listing page

        Returns:
            URL of the next page, or None if there is no next page
        """
        pass

    @abstractmethod
    def _extract_job_title(self, response: scrapy.http.Response) -> str | None:
        """Extract the job title from a job detail page.

        Args:
            response: The HTTP response of the job detail page

        Returns:
            The job title, or None if not found
        """
        pass

    @abstractmethod
    def _extract_job_location(self, response: scrapy.http.Response) -> str | None:
        """Extract the job location from a job detail page.

        Args:
            response: The HTTP response of the job detail page

        Returns:
            The job location, or None if not found
        """
        pass

    @abstractmethod
    def _extract_job_description(self, response: scrapy.http.Response) -> str | None:
        """Extract the job description from a job detail page.

        Args:
            response: The HTTP response of the job detail page

        Returns:
            The job description, or None if not found
        """
        pass
