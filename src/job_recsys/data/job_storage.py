from job_recsys.core.storage.base import Storage
from job_recsys.core.models.job import JobListing
from job_recsys.core.utils import hash_url


class JobStorage:
    def __init__(self, storage: Storage, base_prefix: str = "jobs"):
        self.storage = storage
        self.base_prefix = base_prefix

    def _get_storage_key(self, company: str, url_hash: str) -> str:
        return f"{self.base_prefix}/{company}/{url_hash}"

    def store_job(self, job: JobListing) -> str:
        key = self._get_storage_key(job.metadata.company, job.metadata.url_hash)
        self.storage.save_json(key, job.model_dump())

    def get_job(self, company: str, url_hash: str) -> JobListing:
        key = self._get_storage_key(company, url_hash)
        data = self.storage.get_json(key)
        return JobListing.model_validate(data)

    def job_exists(self, company: str, url: str) -> bool:
        url_hash = hash_url(url)
        key = self._get_storage_key(company, url_hash)
        return self.storage.exists(key)
