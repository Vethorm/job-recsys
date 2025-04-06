from job_recsys.core.storage.base import Storage
from job_recsys.core.models.job import JobListing
from job_recsys.core.utils import hash_url


class JobStorage:
    """Provides a specialized storage interface for job listings.

    Manages storing, retrieving, and checking existence of job listings
    using a generic storage backend. Generates consistent storage keys
    based on company and URL hash.

    Attributes:
        storage (Storage): The underlying storage system used for persistence.
        base_prefix (str): Base path prefix for storing job listings.
    """

    def __init__(self, storage: Storage, base_prefix: str = "jobs"):
        """Initialize a JobStorage instance.

        Args:
            storage: Storage backend to use for job listing persistence
            base_prefix: Base directory or prefix for storing job listings.
                         Defaults to "jobs".
        """
        self.storage = storage
        self.base_prefix = base_prefix

    def _get_storage_key(self, company: str, url_hash: str) -> str:
        """Generate a consistent storage key for a job listing.

        Creates a standardized key path based on base prefix, company, and URL hash.

        Args:
            company: Name of the company posting the job
            url_hash: Unique hash of the job listing's URL

        Returns:
            A formatted storage key string
        """
        return f"{self.base_prefix}/{company}/{url_hash}"

    def store_job(self, job: JobListing) -> str:
        """Store a job listing in the underlying storage system.

        Saves the entire job listing as a JSON document using a
        generated storage key based on company and URL hash.

        Args:
            job: JobListing instance to be stored

        Returns:
            The storage key where the job was saved
        """
        key = self._get_storage_key(job.metadata.company, job.metadata.url_hash)
        return self.storage.save_json(key, job.model_dump())

    def get_job(self, company: str, url_hash: str) -> JobListing:
        """Retrieve a job listing from storage.

        Fetches a previously stored job listing using its company and URL hash.

        Args:
            company: Name of the company that posted the job
            url_hash: Unique hash of the job listing's URL

        Returns:
            The retrieved JobListing instance

        Raises:
            KeyError: If no job listing is found for the given company and URL hash
        """
        key = self._get_storage_key(company, url_hash)
        data = self.storage.get_json(key)
        return JobListing.model_validate(data)

    def job_exists(self, company: str, url: str) -> bool:
        """Check if a job listing exists in storage.

        Determines whether a job listing is already stored based on
        its company and original URL.

        Args:
            company: Name of the company that posted the job
            url: Original URL of the job listing

        Returns:
            True if the job listing exists in storage, False otherwise
        """
        url_hash = hash_url(url)
        key = self._get_storage_key(company, url_hash)
        return self.storage.exists(key)
