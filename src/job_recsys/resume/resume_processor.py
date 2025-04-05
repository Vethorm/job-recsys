import json
from loguru import logger
from pathlib import Path
from job_recsys.embeddings.embedding_models.base import BaseEmbeddingModel
from job_recsys.embeddings.embedding_models.sentence_embedder import (
    SentenceTransformerModel,
    SentenceTransformerModels,
)
from job_recsys.resume.extractor import (
    extract_text_from_pdf,
)  # Assuming this is in 'pdf_extractor.py'


class ResumeEmbeddingProcessor:
    def __init__(
        self,
        embedding_models: dict[str, BaseEmbeddingModel] = None,
        output_dir: str = "./embeddings/resumes",
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_models = embedding_models or {}
        logger.info(
            f"Initialized ResumeEmbeddingProcessor with output_dir={self.output_dir}"
        )

    def generate_resume_embedding(self, resume_text: str) -> dict:
        """Generate embeddings for the provided resume text using all models."""
        embeddings = {}
        for model_name, embedding_model in self.embedding_models.items():
            embeddings[model_name] = embedding_model.generate_embeddings([resume_text])[
                0
            ].values.tolist()
            logger.info(f"Generated embedding for model '{model_name}'")
        return embeddings

    def process_resume(self, pdf_path: str):
        """Extract text from a resume PDF, generate embeddings, and save them."""
        resume_text = extract_text_from_pdf(pdf_path)
        if not resume_text.strip():
            logger.error(f"No text found in the resume: {pdf_path}")
            return

        embeddings = self.generate_resume_embedding(resume_text)

        # Save embeddings to a JSON file
        resume_filename = Path(pdf_path).stem
        output_file = self.output_dir / f"{resume_filename}_embedding.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                {"resume_filename": resume_filename, "embeddings": embeddings},
                f,
                indent=4,
                ensure_ascii=False,
            )
        logger.info(f"Saved resume embeddings to {output_file}")


if __name__ == "__main__":
    embedding_models = {
        SentenceTransformerModels.GTE_MULTILINGUAL_BASE: SentenceTransformerModel(
            SentenceTransformerModels.GTE_MULTILINGUAL_BASE, trust_remote_code=True
        )
    }

    processor = ResumeEmbeddingProcessor(
        embedding_models=embedding_models,
        output_dir="./embeddings/resumes",
    )

    # Example usage
    resume_pdf_path = (
        "./data/Software_Engineering_2.pdf"  # Replace with your PDF file path
    )
    processor.process_resume(resume_pdf_path)
