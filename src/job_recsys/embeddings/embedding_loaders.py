import json
from pathlib import Path
from loguru import logger


class JobEmbeddingLoader:
    def __init__(self, base_dir: str):
        """
        Initializes the loader with the base directory for job embeddings.

        Args:
            base_dir (str): Path to the base directory containing all company subfolders.
        """
        self.base_dir = Path(base_dir)
        logger.info(f"Initialized JobEmbeddingLoader with base_dir={base_dir}")

    def load_embeddings_for_company(self, company: str) -> list[dict]:
        """
        Loads all job embeddings for a specific company.

        Args:
            company (str): The company name (subfolder in the base directory).

        Returns:
            list[dict]: A list of job embedding dictionaries for the specified company.
        """
        company_dir = self.base_dir / company
        if not company_dir.is_dir():
            logger.error(f"Company directory not found: {company_dir}")
            return []

        embeddings = []
        for file in company_dir.glob("*.json"):
            embedding_data = self._load_embedding(file)
            if embedding_data:
                embeddings.append(embedding_data)
        logger.info(f"Loaded {len(embeddings)} embeddings for company: {company}")
        return embeddings

    def load_embeddings_for_companies(self, companies: list[str]) -> list[dict]:
        """
        Loads job embeddings for a subset of companies.

        Args:
            companies (list[str]): List of company names to load embeddings for.

        Returns:
            list[dict]: A combined list of job embedding dictionaries from all specified companies.
        """
        all_embeddings = []
        for company in companies:
            embeddings = self.load_embeddings_for_company(company)
            all_embeddings.extend(embeddings)
        logger.info(f"Loaded embeddings for {len(companies)} companies: {companies}")
        return all_embeddings

    def _load_embedding(self, file_path: Path) -> dict:
        """
        Loads a single embedding from a JSON file.

        Args:
            file_path (Path): Path to the embedding JSON file.

        Returns:
            dict: The embedding data.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load embedding from {file_path}: {e}")
            return None


class ResumeEmbeddingLoader:
    def __init__(self, resume_embeddings_dir: str):
        """
        Initializes the loader with the directory for resume embeddings.

        Args:
            resume_embeddings_dir (str): Path to the directory containing resume embeddings.
        """
        self.resume_embeddings_dir = Path(resume_embeddings_dir)
        logger.info(
            f"Initialized ResumeEmbeddingLoader with resume_embeddings_dir={resume_embeddings_dir}"
        )

    def list_embeddings(self) -> list[str]:
        """
        Lists the filenames of all available resume embeddings.

        Returns:
            list[str]: A list of filenames (without extensions) for resume embeddings.
        """
        resume_files = [file.stem for file in self.resume_embeddings_dir.glob("*.json")]
        logger.info(f"Found {len(resume_files)} resume embedding files.")
        return resume_files

    def load_embedding(self, filename: str) -> dict:
        """
        Loads a single resume embedding based on the filename.

        Args:
            filename (str): Filename (without extension) of the resume embedding to load.

        Returns:
            dict: The embedding data.
        """
        file_path = self.resume_embeddings_dir / f"{filename}.json"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load resume embedding from {file_path}: {e}")
            return None


if __name__ == "__main__":
    # Job Embedding Loader
    job_embeddings_dir = "./embeddings"  # Base directory containing company subfolders
    job_loader = JobEmbeddingLoader(job_embeddings_dir)

    # Load all embeddings for a single company
    airbnb_embeddings = job_loader.load_embeddings_for_company("airbnb")
    logger.info(f"Loaded {len(airbnb_embeddings)} embeddings for Airbnb.")

    # Load embeddings for a subset of companies
    companies = ["airbnb", "google"]
    subset_embeddings = job_loader.load_embeddings_for_companies(companies)
    logger.info(
        f"Loaded {len(subset_embeddings)} embeddings for companies: {companies}"
    )

    # Resume Embedding Loader
    resume_embeddings_dir = (
        "./embeddings/resumes"  # Directory containing resume embeddings
    )
    resume_loader = ResumeEmbeddingLoader(resume_embeddings_dir)

    # List all resume embeddings
    available_resumes = resume_loader.list_embeddings()
    logger.info(f"Available resumes: {available_resumes}")

    # Load a specific resume embedding
    if available_resumes:
        selected_resume = available_resumes[0]  # Replace with the desired filename
        resume_embedding = resume_loader.load_embedding(selected_resume)
        logger.info(f"Loaded resume embedding for: {selected_resume}")
