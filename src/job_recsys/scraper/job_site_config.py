"""Job site configuration for managing different job boards using YAML."""

import os
from enum import Enum
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class SpiderType(str, Enum):
    """Enumeration of available spider types.

    Attributes:
        WORKDAY: For Workday-based job boards
        CONFIGURABLE: For custom job boards that use configurable selectors
        GREENHOUSE: For Greenhouse-based job boards
        LEVER: For Lever-based job boards
        CUSTOM: For fully custom spider implementations
    """

    WORKDAY = "workday"
    CONFIGURABLE = "configurable"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    CUSTOM = "custom"


class JobSiteConfig(BaseModel):
    """Configuration for a job site to be scraped.

    Attributes:
        company: Name of the company
        domain: Primary domain for the job site
        spider_type: Type of spider to use for this job site
        enabled: Whether this job site is enabled for scraping
        start_urls: Optional list of specific start URLs
        allowed_domains: Optional list of additional allowed domains
        config_file: Optional path to a config file (for configurable spiders)
        custom_spider_class: Optional custom spider class name (for custom spiders)
        spider_args: Optional additional arguments to pass to the spider
    """

    company: str
    domain: str
    spider_type: SpiderType
    enabled: bool = True
    start_urls: list[str] | None = None
    allowed_domains: list[str] | None = None
    config_file: str | None = None
    custom_spider_class: str | None = None
    spider_args: dict[str, Any] | None = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_spider_specific_fields(self) -> "JobSiteConfig":
        """Validate that required fields are present for specific spider types."""
        if self.spider_type == SpiderType.CONFIGURABLE and not self.config_file:
            raise ValueError("config_file is required for configurable spiders")

        if self.spider_type == SpiderType.CUSTOM and not self.custom_spider_class:
            raise ValueError("custom_spider_class is required for custom spiders")

        return self


class JobSiteRegistry(BaseModel):
    """Registry of job sites to be scraped.

    Attributes:
        sites: List of job site configurations
    """

    sites: list[JobSiteConfig] = Field(default_factory=list)

    def get_enabled_sites(self) -> list[JobSiteConfig]:
        """Get all enabled job sites.

        Returns:
            List of enabled job site configurations
        """
        return [site for site in self.sites if site.enabled]

    def get_sites_by_spider_type(self, spider_type: SpiderType) -> list[JobSiteConfig]:
        """Get all job sites of a specific spider type.

        Args:
            spider_type: The spider type to filter by

        Returns:
            List of job site configurations with the specified spider type
        """
        return [site for site in self.sites if site.spider_type == spider_type]

    def get_site_by_company(self, company: str) -> JobSiteConfig | None:
        """Get a job site configuration by company name.

        Args:
            company: The company name to search for

        Returns:
            The job site configuration for the specified company, or None if not found
        """
        for site in self.sites:
            if site.company.lower() == company.lower():
                return site
        return None


def load_registry_from_yaml(file_path: str) -> JobSiteRegistry:
    """Load a job site registry from a YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        A JobSiteRegistry loaded from the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file can't be parsed as valid YAML
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Job site registry file not found: {file_path}")

    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)

        return JobSiteRegistry.model_validate(data)
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading job site registry: {e}") from e


def save_registry_to_yaml(registry: JobSiteRegistry, file_path: str) -> None:
    """Save a job site registry to a YAML file.

    Args:
        registry: The JobSiteRegistry to save
        file_path: Path to the YAML file
    """
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

    with open(file_path, "w") as f:
        yaml.dump(registry.model_dump(), f, default_flow_style=False, sort_keys=False)


def merge_registry_with_yaml(registry: JobSiteRegistry, file_path: str) -> JobSiteRegistry:
    """Merge an existing registry with a YAML file.

    Args:
        registry: The existing JobSiteRegistry
        file_path: Path to the YAML file to merge

    Returns:
        A new JobSiteRegistry with the merged configurations
    """
    new_registry = load_registry_from_yaml(file_path)

    existing_sites = {site.company.lower(): site for site in registry.sites}

    merged_sites = []
    for site in new_registry.sites:
        company_lower = site.company.lower()
        if company_lower in existing_sites:
            merged_sites.append(site)
            del existing_sites[company_lower]
        else:
            merged_sites.append(site)

    for site in existing_sites.values():
        merged_sites.append(site)

    return JobSiteRegistry(sites=merged_sites)
