"""Idea for configurable job board spider with YAML-based configuration. Idk if it works."""


import scrapy
import yaml
from loguru import logger

from job_recsys.data.job_storage import JobStorage
from job_recsys.scraper.spiders.base_spider import BaseJobSpider


class ConfigurableJobSpider(BaseJobSpider):
    """A configurable spider for scraping job boards based on YAML configuration.

    This spider allows for configuration of all selectors via a YAML config file,
    making it adaptable to various job board structures without code changes.

    Attributes:
        name (str): Spider name
        allowed_domains (list): Domains this spider is allowed to crawl
        config (dict): Configuration containing all CSS selectors and patterns
    """

    name = "configurable_job_spider"

    def __init__(self, company: str, job_storage: JobStorage, config_file: str, *args, **kwargs):
        """Initialize the configurable job spider.

        Args:
            company: Name of the company whose jobs are being scraped
            job_storage: Storage instance for saving job listings
            config_file: Path to YAML configuration file with selectors
            *args: Additional positional arguments passed to parent constructor
            **kwargs: Additional keyword arguments passed to parent constructor
        """
        super().__init__(company=company, job_storage=job_storage, *args, **kwargs)

        try:
            with open(config_file, "r") as f:
                self.config = yaml.safe_load(f)

            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_file}: {e}")
            self.config = {}
            raise ValueError(f"Failed to load configuration: {e}") from e

        if "allowed_domains" in self.config:
            self.allowed_domains = self.config["allowed_domains"]

        if not self.start_urls and "start_urls" in self.config:
            self.start_urls = self.config["start_urls"]

        logger.info(f"Initialized configurable spider for {company} with config {config_file}")

    def _is_sitemap(self, response: scrapy.http.Response) -> bool:
        """Determine if the response is a sitemap.

        Args:
            response: The HTTP response to check

        Returns:
            True if the response is a sitemap, False otherwise
        """
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", "ignore")

        sitemap_patterns = self.config.get("sitemap_patterns", ["<urlset", "<sitemapindex"])

        is_xml = "xml" in content_type.lower() or response.url.endswith(".xml")
        has_sitemap_element = any(pattern.encode() in response.body for pattern in sitemap_patterns)

        return is_xml and has_sitemap_element

    def _is_job_listing_page(self, response: scrapy.http.Response) -> bool:
        """Determine if the response is a job listing page with multiple jobs.

        Args:
            response: The HTTP response to check

        Returns:
            True if the response is a job listing page, False otherwise
        """
        selectors = self.config.get("job_listing_page_selectors", [])

        for selector in selectors:
            if response.css(selector):
                return True
