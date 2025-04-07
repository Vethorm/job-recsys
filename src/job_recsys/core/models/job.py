from enum import StrEnum, auto

from pydantic import BaseModel, Field

from job_recsys.core.utils import hash_url


class JobStatus(StrEnum):
    """Enumeration representing the current status of a job listing.

    Attributes:
        ACTIVE: Indicates the job listing is still available and open.
        EXPIRED: Indicates the job listing is no longer available.
    """

    ACTIVE = auto()  # job listing is still up
    EXPIRED = auto()  # job listing is no longer available


class ProcessingStatus(BaseModel):
    """Model representing the processing status of a job listing.

    Attributes:
        parsed (bool): Indicates whether the job listing has been parsed. Defaults to False.
        embeddings_generated (bool): Indicates whether embeddings have been generated for the job listing. Defaults to False.
    """

    parsed: bool = False
    embeddings_generated: bool = False


class JobMetadata(BaseModel):
    """Model containing metadata information for a job listing.

    Attributes:
        source_url (str): The original URL of the job listing.
        url_hash (str): A unique hash generated from the source URL.
        company (str): The name of the company posting the job.
        first_seen (datetime): Timestamp of when the job listing was first discovered. Defaults to current time.
        last_updated (datetime): Timestamp of the most recent update. Defaults to current time.
        version (int): Version number of the job listing metadata. Defaults to 1.
        status (JobStatus): Current status of the job listing.
        processing_status (ProcessingStatus): Current processing status of the job listing.
            Defaults to a new ProcessingStatus.
    """

    source_url: str
    url_hash: str
    company: str
    # first_seen: datetime = Field(default_factory=datetime.now)
    # last_updated: datetime = Field(default_factory=datetime.now)
    version: int = 1
    status: JobStatus
    processing_status: ProcessingStatus = Field(default_factory=ProcessingStatus)


class JobData(BaseModel):
    """Model representing the core data of a job listing.

    Attributes:
        title (Optional[str]): The title of the job. Can be None if not available.
        location (Optional[str]): The location of the job. Can be None if not available.
        description (Optional[str]): The detailed description of the job. Can be None if not available.
        raw_html (Optional[str]): The raw HTML content of the job listing. Can be None if not available.
    """

    title: str | None = None
    location: str | None = None
    description: str | None = None
    raw_html: str | None = None


class JobListing(BaseModel):
    """Model representing a complete job listing with its data and metadata.

    Attributes:
        data (JobData): The core information about the job.
        metadata (JobMetadata): Metadata associated with the job listing.

    Methods:
        create: Class method to create a new JobListing instance.
        update_status: Update the job listing's status.
        update_processing_status: Update the job listing's processing status.
        get_storage_key: Generate a storage key for the job listing.
    """

    data: JobData
    metadata: JobMetadata

    @classmethod
    def create(cls, url: str, company: str, job_data: JobData) -> "JobListing":
        """Create a new JobListing instance.

        Args:
            url (str): The source URL of the job listing.
            company (str): The name of the company posting the job.
            job_data (JobData): The data associated with the job listing.

        Returns:
            JobListing: A new JobListing instance with generated metadata.
        """
        url_hash = hash_url(url)

        metadata = JobMetadata(source_url=url, url_hash=url_hash, company=company, status=JobStatus.ACTIVE)
        return cls(data=job_data, metadata=metadata)

    def update_status(self, status: JobStatus) -> None:
        """Update the status of the job listing.

        Args:
            status (JobStatus): The new status to set for the job listing.
        """
        if status != self.metadata.status:
            self.metadata.status = status

    def update_processing_status(self, processing_status: ProcessingStatus) -> None:
        """Update the processing status of the job listing.

        Args:
            processing_status (ProcessingStatus): The new processing status to set.
        """
        if processing_status != self.metadata.processing_status:
            self.metadata.processing_status = processing_status

    def get_storage_key(self, base_prefix: str = "jobs") -> str:
        """Generate a storage key for the job listing.

        Args:
            base_prefix (str, optional): The base prefix for the storage key. Defaults to "jobs".

        Returns:
            str: A storage key in the format "{base_prefix}/{company}/{url_hash}.json"
        """
        return f"{base_prefix}/{self.metadata.company}/{self.metadata.url_hash}.json"

    def __str__(self) -> str:
        """Provide a string representation of the job listing.

        Returns:
            str: A human-readable string describing the job listing.
        """
        title = self.data.title or "Untitled Job"
        return f"{title} at {self.metadata.company} ({self.metadata.status.value}, v{self.metadata.version})"
