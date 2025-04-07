"""Workday job listing spider implementation."""

import re
from typing import Generator
from urllib.parse import urljoin

import scrapy
from loguru import logger

from job_recsys.data.job_storage import JobStorage
from job_recsys.scraper.spiders.base_spider import BaseJobSpider


class WorkdaySpider(BaseJobSpider):
    """Spider for scraping job listings from Workday career sites.

    Specialized implementation for Workday-powered job boards, which typically
    have a consistent structure across different companies.

    Attributes:
        name (str): Spider name
        allowed_domains (list): Domains this spider is allowed to crawl
    """

    name = "workday_spider"

    def __init__(self, company: str, job_storage: JobStorage, workday_domain: str, *args, **kwargs):
        """Initialize the Workday spider.

        Args:
            company: Name of the company whose jobs are being scraped
            job_storage: Storage instance for saving job listings
            workday_domain: The Workday domain for this company (e.g., "company.workday.com")
            *args: Additional positional arguments passed to parent constructor
            **kwargs: Additional keyword arguments passed to parent constructor
        """
        super().__init__(company=company, job_storage=job_storage, *args, **kwargs)

        self.allowed_domains = [workday_domain]

        robots_url = f"https://{workday_domain}/robots.txt"
        self.start_urls = [robots_url]

        logger.info(f"Initialized Workday spider for {company} with domain {workday_domain}")

    def parse(self, response: scrapy.http.Response) -> Generator:
        """Parse response based on its type.

        Extends the base parse method to handle robots.txt files.
        """
        if response.url.endswith("/robots.txt"):
            yield from self.parse_robots_txt(response)
        else:
            yield from super().parse(response)

    def parse_robots_txt(self, response: scrapy.http.Response) -> Generator:
        """Parse robots.txt to extract sitemap URL.

        Args:
            response: The HTTP response containing robots.txt

        Yields:
            Request for the sitemap
        """
        sitemap_matches = re.findall(r"Sitemap:\s*(https?://[^\s]+)", response.text)

        if sitemap_matches:
            sitemap_url = sitemap_matches[0].strip()
            logger.info(f"Found sitemap URL in robots.txt: {sitemap_url}")
            yield scrapy.Request(url=sitemap_url, callback=self.parse_sitemap)
        else:
            main_url = f"https://{self.allowed_domains[0]}/careers"
            logger.info(f"No sitemap found in robots.txt, trying main page: {main_url}")
            yield scrapy.Request(url=main_url, callback=self.parse_listing_page)

    def parse_sitemap(self, response: scrapy.http.Response) -> Generator:
        """Parse sitemap XML to extract job listing URLs with enhanced debugging.

        Args:
            response: The HTTP response containing the sitemap

        Yields:
            Requests to job detail pages
        """
        logger.debug(f"Sitemap URL: {response.url}")
        logger.debug(f"Response status: {response.status}")

        body_preview = response.body[:500].decode("utf-8", errors="ignore")
        logger.debug(f"Response body preview: \n{body_preview}")

        xpath_patterns = ["//urlset/url/loc/text()", "//url/loc/text()", "//loc/text()"]

        all_urls = []
        for pattern in xpath_patterns:
            urls = response.xpath(pattern).getall()
            logger.debug(f"XPath pattern '{pattern}' found {len(urls)} URLs")
            if urls:
                for i, url in enumerate(urls[:3]):
                    logger.debug(f"Sample URL {i + 1}: {url}")
                all_urls = urls
                break

        if not all_urls:
            logger.warning("No URLs found with standard XPath patterns, trying regex approach")
            body_text = response.body.decode("utf-8", errors="ignore")
            url_matches = re.findall(r"<loc>(https?://[^<]+)</loc>", body_text)
            all_urls = url_matches
            logger.debug(f"Regex found {len(all_urls)} URLs")

        job_urls = []
        job_patterns = [
            r"/job/",
            r"JR\d+",  # Often job IDs in Workday have this format
            r"jobReqId=",
        ]

        for url in all_urls:
            is_job_url = any(re.search(pattern, url) for pattern in job_patterns)
            if is_job_url:
                job_urls.append(url)

        filtered_urls = self._filter_existing_urls(job_urls)

        logger.info(f"Found {len(job_urls)} job URLs out of {len(all_urls)} total URLs")
        logger.info(f"Filtered urls to {len(filtered_urls)} out of {len(job_urls)}")

        for url in filtered_urls:
            yield scrapy.Request(url=url, callback=self.parse_job_detail)

    def _is_sitemap(self, response: scrapy.http.Response) -> bool:
        """Determine if the response is a sitemap.

        Args:
            response: The HTTP response to check

        Returns:
            True if the response is a sitemap, False otherwise
        """
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", "ignore")

        if "xml" in content_type.lower() or response.url.endswith(".xml"):
            return b"<urlset" in response.body or b"<sitemapindex" in response.body

        return False

    def _is_job_listing_page(self, response: scrapy.http.Response) -> bool:
        """Determine if the response is a job listing page with multiple jobs.

        For Workday, checks if page contains the typical job search results structure.

        Args:
            response: The HTTP response to check

        Returns:
            True if the response is a job listing page, False otherwise
        """
        return bool(response.css("div.css-jobs-result-container")) or bool(response.css('div[data-list-type="jobs"]'))

    def _extract_job_urls_from_sitemap(self, response: scrapy.http.Response) -> list[str]:
        """Extract job detail URLs from a sitemap.

        Args:
            response: The HTTP response containing the sitemap

        Returns:
            List of job detail URLs
        """
        job_urls = []

        all_urls = response.xpath("//urlset/url/loc/text()").getall()

        if not all_urls:
            all_urls = response.xpath("//loc/text()").getall()

        logger.info(f"Found {len(all_urls)} URLs in sitemap")

        job_pattern = r"/job/"
        job_urls = [url for url in all_urls if re.search(job_pattern, url)]

        logger.info(f"Extracted {len(job_urls)} job URLs from sitemap")
        if not job_urls and all_urls:
            logger.warning(f"No job URLs found matching pattern. Sample URL: {all_urls[0]}")

        return job_urls

    def _extract_job_urls_from_listing(self, response: scrapy.http.Response) -> list[str]:
        """Extract job detail URLs from a listing page.

        Args:
            response: The HTTP response containing job listings

        Returns:
            List of job detail URLs
        """
        job_urls = []

        selectors = [
            "a.css-jobs-link::attr(href)",
            "div.job-post a::attr(href)",
            'div[data-automation-id="jobTitle"] a::attr(href)',
        ]

        for selector in selectors:
            relative_urls = response.css(selector).getall()
            if relative_urls:
                job_urls = [urljoin(response.url, url) for url in relative_urls]
                break

        logger.info(f"Extracted {len(job_urls)} job URLs from listing page")
        return job_urls

    def _get_next_page_url(self, response: scrapy.http.Response) -> str | None:
        """Get the URL of the next page of job listings, if any.

        Args:
            response: The HTTP response of the current listing page

        Returns:
            URL of the next page, or None if there is no next page
        """
        next_page_selectors = [
            'a[data-automation-id="paginationNextButton"]:not([disabled])::attr(href)',
            "button.css-next-page:not([disabled]) + a::attr(href)",
            "a.css-pagination-next:not(.disabled)::attr(href)",
        ]

        for selector in next_page_selectors:
            next_page = response.css(selector).get()
            if next_page:
                return urljoin(response.url, next_page)

        return None

    def _extract_job_title(self, response: scrapy.http.Response) -> str | None:
        """Extract the job title from a job detail page.

        Args:
            response: The HTTP response of the job detail page

        Returns:
            The job title, or None if not found
        """
        title_selectors = ['h1[data-automation-id="jobTitle"]::text', "h1.css-job-title::text", "h1.job-title::text"]

        for selector in title_selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()

        return None

    def _extract_job_location(self, response: scrapy.http.Response) -> str | None:
        """Extract the job location from a job detail page.

        Args:
            response: The HTTP response of the job detail page

        Returns:
            The job location, or None if not found
        """
        location_selectors = [
            'div[data-automation-id="jobLocationList"]::text',
            "span.css-job-location::text",
            "div.job-location::text",
        ]

        for selector in location_selectors:
            location = response.css(selector).get()
            if location:
                return location.strip()

        return None

    def _extract_job_description(self, response: scrapy.http.Response) -> str | None:
        """Extract the job description from a job detail page.

        Args:
            response: The HTTP response of the job detail page

        Returns:
            The job description, or None if not found
        """
        description_selectors = [
            'div[data-automation-id="jobDescription"]',
            "div.css-job-description",
            "div.job-description",
        ]

        for selector in description_selectors:
            description_element = response.css(selector)
            if description_element:
                description_text = " ".join(description_element.xpath(".//text()").getall())
                description_text = re.sub(r"\s+", " ", description_text).strip()
                return description_text

        return None
