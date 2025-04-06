from enum import StrEnum, auto
from pydantic import BaseModel, Field
import hashlib
from datetime import datetime
from typing import Optional
from job_recsys.core.utils import hash_url


class JobStatus(StrEnum):
    ACTIVE = auto()  # job listing is still up
    EXPIRED = auto()  # job listing is no longer available


class ProcessingStatus(BaseModel):
    parsed: bool = False
    embeddings_generated: bool = False


class JobMetadata(BaseModel):
    source_url: str
    url_hash: str
    company: str
    first_seen: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: int = 1
    status: JobStatus
    processing_status: ProcessingStatus = Field(default_factory=ProcessingStatus)


class JobData(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    raw_html: Optional[str] = None


class JobListing(BaseModel):
    data: JobData
    metadata: JobMetadata

    @classmethod
    def create(cls, url: str, company: str, job_data: JobData) -> "JobListing":
        url_hash = hash_url(url)

        metadata = JobMetadata(source_url=url, url_hash=url_hash, company=company)
        return cls(data=job_data, metadata=metadata)

    def update_status(self, status: JobStatus) -> None:
        if status != self.metadata.status:
            self.metadata.status = status

    def update_processing_status(self, processing_status: ProcessingStatus) -> None:
        if processing_status != self.metadata.processing_status:
            self.metadata.processing_status = processing_status

    def get_storage_key(self, base_prefix: str = "jobs") -> str:
        return f"{base_prefix}/{self.metadata.company}/{self.metadata.url_hash}.json"

    def __str__(self) -> str:
        title = self.data.title or "Untitled Job"
        return f"{title} at {self.metadata.company} ({self.metadata.status.value}, v{self.metadata.version})"
