"""Script to run job scrapers based on YAML job site registry."""

import argparse
import importlib
import os
import sys
from pathlib import Path

from loguru import logger
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from job_recsys.core.storage.filesystem import FileSystemStorage
from job_recsys.data.job_storage import JobStorage
from job_recsys.scraper.job_site_config import JobSiteConfig, JobSiteRegistry, SpiderType, load_registry_from_yaml
from job_recsys.scraper.spiders.base_spider import BaseJobSpider


def setup_logging(log_level: str = "INFO", log_file: str | None = None):
    """Configure logging with loguru.

    Args:
        log_level: Logging level to use
        log_file: Optional file path for logging
    """
    logger.remove()  # Remove default handler

    # Add stderr handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    # Add file handler if specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logger.add(
            log_file,
            rotation="10 MB",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )
    else:
        # Default log file with timestamp
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        logger.add(
            "logs/spider_{time}.log",
            rotation="10 MB",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )


def get_spider_class(site_config: JobSiteConfig) -> type[BaseJobSpider]:
    """Get the appropriate spider class for a job site.

    Args:
        site_config: Job site configuration

    Returns:
        Spider class to use for the job site

    Raises:
        ValueError: If the spider type is not supported or the spider class cannot be found
    """
    from job_recsys.scraper.spiders.configurable_spider import ConfigurableJobSpider
    from job_recsys.scraper.spiders.workday_spider import WorkdaySpider

    if site_config.spider_type == SpiderType.WORKDAY:
        return WorkdaySpider
    elif site_config.spider_type == SpiderType.CONFIGURABLE:
        return ConfigurableJobSpider
    elif site_config.spider_type == SpiderType.CUSTOM:
        if not site_config.custom_spider_class:
            raise ValueError(f"No custom_spider_class specified for {site_config.company}")

        try:
            module_name = f"job_recsys.scraper.{site_config.custom_spider_class.lower()}"
            module = importlib.import_module(module_name)
            spider_class = getattr(module, site_config.custom_spider_class)
            return spider_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Could not import custom spider class {site_config.custom_spider_class}: {e!s}") from e
    else:
        raise ValueError(f"Unsupported spider type: {site_config.spider_type}")


def get_spider_kwargs(site_config: JobSiteConfig, job_storage: JobStorage) -> dict:
    """Get keyword arguments for a spider based on job site configuration.

    Args:
        site_config: Job site configuration
        job_storage: Storage instance for job listings

    Returns:
        Dictionary of keyword arguments for the spider
    """
    kwargs = {
        "company": site_config.company,
        "job_storage": job_storage,
    }

    if site_config.start_urls:
        kwargs["start_urls"] = site_config.start_urls

    if site_config.spider_type == SpiderType.WORKDAY:
        kwargs["workday_domain"] = site_config.domain
    elif site_config.spider_type == SpiderType.CONFIGURABLE:
        if not site_config.config_file:
            raise ValueError(f"No config_file specified for {site_config.company}")

        config_path = Path(site_config.config_file)
        if not config_path.is_absolute():
            scraper_config_path = Path(__file__).parent.parent / "scraper" / "configs" / config_path.name
            if scraper_config_path.exists():
                kwargs["config_file"] = str(scraper_config_path)
            else:
                kwargs["config_file"] = site_config.config_file
        else:
            kwargs["config_file"] = site_config.config_file

    if site_config.spider_args:
        kwargs.update(site_config.spider_args)

    return kwargs


def parse_args():
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(description="Run job spiders based on YAML job site registry")

    parser.add_argument(
        "--registry", type=str, default="configs/job_sites.yaml", help="Path to job site registry YAML file"
    )

    parser.add_argument(
        "--company", type=str, help="Specific company to scrape (if omitted, scrapes all enabled sites)"
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

    parser.add_argument(
        "--log-file", type=str, help="Path to log file (if omitted, logs to logs/spider_[timestamp].log)"
    )

    parser.add_argument(
        "--max-items", type=int, default=None, help="Maximum number of items to scrape per spider (for testing)"
    )

    parser.add_argument(
        "--respect-robots", action="store_true", help="Respect robots.txt rules (recommended for production)"
    )

    parser.add_argument("--list-companies", action="store_true", help="List all companies in the registry and exit")

    return parser.parse_args()


def list_companies(registry: JobSiteRegistry):
    """List all companies in the registry.

    Args:
        registry: Job site registry
    """
    print("\nAvailable companies in the registry:")
    print("-" * 40)
    print(f"{'COMPANY':<30} {'TYPE':<15} {'ENABLED':<10}")
    print("-" * 40)

    for site in sorted(registry.sites, key=lambda s: s.company):
        enabled = "Yes" if site.enabled else "No"
        print(f"{site.company:<30} {site.spider_type.value:<15} {enabled:<10}")

    print("\nTotal:", len(registry.sites), "companies")
    print("Enabled:", len(registry.get_enabled_sites()), "companies")


def main():
    """Main entry point for the script."""
    args = parse_args()

    setup_logging(args.log_level, args.log_file)

    try:
        registry_path = args.registry

        logger.info(f"Loading job site registry from: {registry_path}")
        registry = load_registry_from_yaml(registry_path)
        logger.info(f"Loaded job site registry with {len(registry.sites)} sites")

        if args.list_companies:
            list_companies(registry)
            return

    except Exception as e:
        logger.error(f"Failed to load job site registry: {e!s}")
        return

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
            "ROBOTSTXT_OBEY": args.respect_robots,
            "CONCURRENT_REQUESTS": 4,
            "DOWNLOAD_DELAY": 1.5,  # 1.5 seconds delay to be respectful
            "COOKIES_ENABLED": True,
            "RETRY_TIMES": 3,
            "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
            "DOWNLOAD_TIMEOUT": 60,  # 60 seconds timeout
            "FEED_EXPORT_ENCODING": "utf-8",
        }
    )

    process = CrawlerProcess(settings)

    sites_to_scrape = []
    if args.company:
        site = registry.get_site_by_company(args.company)
        if site and site.enabled:
            sites_to_scrape.append(site)
        else:
            logger.error(f"Company {args.company} not found or not enabled in registry")
            return
    else:
        sites_to_scrape = registry.get_enabled_sites()

    if not sites_to_scrape:
        logger.warning("No sites to scrape")
        return

    for site in sites_to_scrape:
        try:
            spider_class = get_spider_class(site)

            spider_kwargs = get_spider_kwargs(site, job_storage)

            logger.info(f"Starting spider for {site.company} ({site.spider_type.value})")
            process.crawl(spider_class, **spider_kwargs)

        except Exception as e:
            logger.error(f"Failed to set up spider for {site.company}: {e!s}")

    if process.crawlers:
        logger.info(f"Starting crawl with {len(process.crawlers)} spiders")
        process.start()
        logger.info("All spiders completed")
    else:
        logger.warning("No spiders were started")


if __name__ == "__main__":
    main()
    """
    # Run all enabled job spiders
    run-job-spiders --registry configs/job_sites.yaml

    # Run a specific company's spider
    run-job-spiders --company NVIDIA --log-level DEBUG

    # List all companies in the registry
    run-job-spiders --list-companies
    """
