from pydantic import BaseModel, HttpUrl
from pathlib import Path
from loguru import logger
import json


class Job(BaseModel):
    """Pydantic schema for job data."""

    url: HttpUrl
    job_description: str

    def to_serializable_dict(self):
        """Converts the model to a dict with serializable fields."""
        return {
            "url": str(self.url),  # Convert HttpUrl to string
            "job_description": self.job_description,
        }

    def to_json(self, file_path: Path):
        """Exports the job data to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(
                self.to_serializable_dict(), json_file, indent=4, ensure_ascii=False
            )
        logger.info(f"Saved job data to {file_path}")


class JobEmbedding(BaseModel):
    job_url: HttpUrl
    embeddings: dict[str, list[float]]  # Keyed by model name

    def to_serializable_dict(self):
        return {
            "job_url": str(self.job_url),
            "embeddings": self.embeddings,
        }

    def to_json(self, file_path: Path):
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(
                self.to_serializable_dict(), json_file, indent=4, ensure_ascii=False
            )
        logger.info(f"Saved embedding data to {file_path}")
