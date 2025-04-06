# jobmatch_scraper/spiders/greenhouse_spider.py
from urllib.parse import urljoin

import scrapy

from .base_spider import BaseJobSpider


class GreenhouseSpider(BaseJobSpider):
    name = "greenhouse"

    def __init__(self, start_url=None, company=None, *args, **kwargs):
        super(GreenhouseSpider, self).__init__(company=company, *args, **kwargs)

        if start_url:
            self.start_urls = [start_url]

    def parse(self, response):
        """Entry point for processing a career page."""
        # Extract all job URLs from the page
        job_links = response.css(".opening a::attr(href), .position a::attr(href)").getall()

        for link in job_links:
            absolute_url = urljoin(response.url, link)
            yield scrapy.Request(absolute_url, callback=self.parse_job)

    def parse_job(self, response):
        """Parse a Greenhouse job listing page."""
        job = super().parse_job(response)

        # Extract job details using CSS selectors
        job["title"] = response.css("h1.app-title::text, h1.opening-title::text").get()
        job["location"] = response.css(".location::text, .job-location::text").get()
        job["department"] = response.css(".department::text").get()

        # Extract description
        description = response.css("#content, .job-description, #job-description")
        if description:
            job["description"] = description.get()

        # Extract requirements
        requirements = []
        for ul in response.css("#content ul, .job-description ul"):
            prev_heading = ul.xpath("./preceding-sibling::*[self::h2 or self::h3 or self::strong][1]")
            if prev_heading and any(
                term in prev_heading.css("::text").get("").lower()
                for term in ["require", "qualification", "skill", "experience"]
            ):
                for li in ul.css("li::text").getall():
                    if li.strip():
                        requirements.append(li.strip())

        job["requirements"] = requirements

        return job
