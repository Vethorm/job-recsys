# jobmatch_scraper/spiders/base_spider.py
from datetime import datetime

import scrapy

from job_recsys.scraper.spiders.items import JobItem


class BaseJobSpider(scrapy.Spider):
    name = "base_job_spider"

    def __init__(self, company=None, *args, **kwargs):
        super(BaseJobSpider, self).__init__(*args, **kwargs)
        self.company = company

    def parse(self, response):
        """Default implementation to be overridden by specific spiders."""
        pass

    def extract_job_urls(self, response):
        """Should be implemented by child classes to extract job URLs."""
        raise NotImplementedError

    def parse_job(self, response):
        """Default job parser that child classes can override."""
        job = JobItem()
        job["url"] = response.url
        job["company"] = self.company
        job["raw_html"] = response.body
        job["scrape_date"] = datetime.now().isoformat()
        return job
