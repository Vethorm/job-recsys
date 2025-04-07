"""Script to run the Workday spider for a specific company."""

import argparse
from pathlib import Path

from loguru import logger
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from job_recsys.core.storage.filesystem import FileSystemStorage
from job_recsys.data.job_storage import JobStorage
from job_recsys.scraper.spiders.workday_spider import WorkdaySpider


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="Run Workday spider for a specific company")

    parser.add_argument("--company", type=str, required=True, help="Name of the company to scrape")

    parser.add_argument(
        "--domain", type=str, required=True, help="Workday domain for the company (e.g., company.workday.com)"
    )

    parser.add_argument(
        "--storage-dir", type=str, default="./data/jobs", help="Directory to store scraped job listings"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level",
    )

    parser.add_argument("--max-items", type=int, default=None, help="Maximum number of items to scrape (for testing)")

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()

    storage_dir = Path(args.storage_dir).absolute()
    logger.info(f"Using storage directory: {storage_dir}")

    file_storage = FileSystemStorage(base_dir=str(storage_dir))
    job_storage = JobStorage(storage=file_storage)

    settings = get_project_settings()
    settings.update(
        {
            "LOG_LEVEL": args.log_level,
            "CLOSESPIDER_ITEMCOUNT": args.max_items,
            "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "ROBOTSTXT_OBEY": True,
            "CONCURRENT_REQUESTS": 4,
            "DOWNLOAD_DELAY": 2,
            "COOKIES_ENABLED": True,
            "RETRY_TIMES": 3,
            "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
            "FEED_EXPORT_ENCODING": "utf-8",
        }
    )

    process = CrawlerProcess(settings)

    logger.info(f"Starting spider for {args.company} at {args.domain}")
    process.crawl(WorkdaySpider, company=args.company, job_storage=job_storage, workday_domain=args.domain)

    process.start()

    logger.info("Spider run completed")


if __name__ == "__main__":
    main()
    """
    uv run python -m job_recsys.scripts.run_spider \
        --company "Acme Inc" \
        --domain "acme.workday.com" \
        --storage-dir "./data/jobs" \
        --log-level "INFO" \
        --max-items 100
    """
