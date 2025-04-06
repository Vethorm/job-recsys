# job_recsys/scraper/pipelines.py
from typing import Dict, Any, Optional

from itemadapter import ItemAdapter
import scrapy
import loguru

from job_recsys.core.utils import hash_url


class JobStoragePipeline:
    """Pipeline to store job listings in the data repository.

    This pipeline handles the storage of scraped job items,
    with additional processing and deduplication logic.
    """

    def __init__(self, job_storage):
        """Initialize the pipeline with a job storage mechanism.

        Args:
            job_storage: Storage interface for job listings.
        """
        self.job_storage = job_storage
        self.logger = loguru.logger.bind(pipeline="job_storage")

    @classmethod
    def from_crawler(cls, crawler):
        """Class method to create a pipeline instance from a Scrapy crawler.

        Args:
            crawler (scrapy.crawler.Crawler): Scrapy crawler instance.

        Returns:
            JobStoragePipeline: Configured pipeline instance.
        """
        # Import storage dependencies here to avoid circular imports
        from job_recsys.data.job_storage import JobStorage
        from job_recsys.core.storage.filesystem import FileSystemStorage

        # Allow configuration of storage path via crawler settings
        storage_path = crawler.settings.get("JOB_STORAGE_PATH", "/tmp/jobmatch_data")
        storage = FileSystemStorage(storage_path)
        job_storage = JobStorage(storage)

        # Create pipeline instance
        pipeline = cls(job_storage)

        # Log pipeline initialization
        pipeline.logger.info(f"Initialized JobStoragePipeline with storage at {storage_path}")

        return pipeline

    def _clean_job_data(self, job_data: dict[str, Any]) -> dict[str, Any]:
        """Clean and prepare job data for storage.

        Args:
            job_data (Dict[str, Any]): Raw job data from scraper.

        Returns:
            Dict[str, Any]: Cleaned job data.
        """
        # Remove any None or empty string values
        cleaned_data = {k: v for k, v in job_data.items() if v is not None and v != ""}

        # Ensure key fields are present
        required_fields = ["url", "company"]
        for field in required_fields:
            if field not in cleaned_data:
                cleaned_data[field] = "Unknown"

        return cleaned_data

    def process_item(self, item: scrapy.Item, spider: scrapy.Spider):
        """Process and store a scraped job item.

        Args:
            item (scrapy.Item): Scraped job item.
            spider (scrapy.Spider): Spider that scraped the item.

        Returns:
            scrapy.Item: The original item (for further processing).
        """
        try:
            # Convert Scrapy item to dict
            job_data = dict(ItemAdapter(item).asdict())

            # Clean the job data
            cleaned_job_data = self._clean_job_data(job_data)

            # Generate unique hash for the job URL
            job_hash = hash_url(cleaned_job_data.get("url", ""))

            # Import JobListing here to avoid potential circular imports
            from job_recsys.core.models.job import JobListing

            # Extract critical fields
            url = cleaned_job_data.pop("url", "Unknown")
            company = cleaned_job_data.pop("company", "Unknown")

            # Create job listing
            job = JobListing.create(url=url, company=company, job_data=cleaned_job_data)

            # Log job details
            self.logger.info(f"Processing job: {job.title} at {company} (Hash: {job_hash})")

            # Store job in repository
            self.job_storage.store_job(job)

            return item

        except Exception as e:
            # Log any errors during processing
            self.logger.error(f"Error processing job item: {e}")
            # Optionally, you could raise or drop the item based on your requirements
            raise scrapy.exceptions.DropItem(f"Error processing job: {e}") from e

    def close_spider(self, spider: scrapy.Spider):
        """Hook method called when spider closes.

        Args:
            spider (scrapy.Spider): Closed spider instance.
        """
        self.logger.info(f"Spider {spider.name} closed. Performing cleanup.")
        # Any final cleanup or summary logging can be added here
