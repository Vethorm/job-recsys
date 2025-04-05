from pathlib import Path
from loguru import logger
import numpy as np
import json
import hashlib
from job_recsys.embeddings.embedding_models.base import BaseEmbeddingModel
from job_recsys.embeddings.embedding_models.sentence_embedder import (
    SentenceTransformerModel,
    SentenceTransformerModels,
)


class JobEmbeddingProcessor:
    def __init__(
        self,
        data_dir: str,
        output_dir: str = "./embeddings",
        embedding_models: dict[str, BaseEmbeddingModel] = None,
    ):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_models = embedding_models or {}
        logger.info(
            f"Initialized JobEmbeddingProcessor with data_dir={self.data_dir}, output_dir={self.output_dir}"
        )

    def hash_url(self, url: str) -> str:
        """Generate a unique hash for the job URL."""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def load_job_data(self) -> list[dict]:
        """Load all job data from the specified directory."""
        jobs = []
        for file in self.data_dir.glob("*.json"):
            logger.info(f"Loading job data from {file}")
            with open(file, "r", encoding="utf-8") as f:
                job_data = json.load(f)
                jobs.append(job_data)
        logger.info(f"Loaded {len(jobs)} job records.")
        return jobs

    def update_or_create_embedding(
        self, url: str, job_description: str, overwrite: bool = False
    ):
        """Updates or creates a JSON file with embeddings for a given job."""
        hashed_filename = self.hash_url(url) + ".json"
        file_path = self.output_dir / hashed_filename

        # Load existing data if the file already exists
        if file_path.exists():
            logger.info(f"File for {url} already exists. Updating embeddings...")
            with open(file_path, "r", encoding="utf-8") as json_file:
                existing_data = json.load(json_file)
        else:
            logger.info(f"Creating a new file for {url}.")
            existing_data = {"job_url": url, "embeddings": {}}

        # Add or update embeddings from the current models
        for model_name, embedding_model in self.embedding_models.items():
            if model_name not in existing_data["embeddings"] or overwrite:
                # Generate new embedding and update
                vector = embedding_model.generate_embeddings([job_description])[0]
                existing_data["embeddings"][model_name] = vector.values.tolist()
                logger.info(
                    f"Added/Updated embedding for model '{model_name}' in {file_path}"
                )

        # Save the updated data back to the file
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(existing_data, json_file, indent=4, ensure_ascii=False)
        logger.info(f"Saved updated embedding data to {file_path}")

    def process_jobs(self, overwrite: bool = False):
        """Process all jobs, generate embeddings, and update or create JSON files."""
        jobs = self.load_job_data()

        for job in jobs:
            job_url = job["url"]
            job_description = job["job_description"]
            self.update_or_create_embedding(
                job_url, job_description, overwrite=overwrite
            )

        logger.info(f"Processed and updated embeddings for {len(jobs)} jobs.")


if __name__ == "__main__":
    # Example embedding models
    embedding_models = {
        SentenceTransformerModels.GTE_MULTILINGUAL_BASE: SentenceTransformerModel(
            SentenceTransformerModels.GTE_MULTILINGUAL_BASE, trust_remote_code=True
        )
    }
    company = "etsy"

    processor = JobEmbeddingProcessor(
        data_dir=f"./data/{company}",
        output_dir=f"./embeddings/{company}",
        embedding_models=embedding_models,
    )
    processor.process_jobs()
