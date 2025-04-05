from job_recsys.embeddings.embedding_models.base import BaseEmbeddingModel, Vector
from sentence_transformers import SentenceTransformer

from loguru import logger


class SentenceTransformerModels:
    ALL_MINI_L6_V2 = "all-MiniLM-L6-v2"
    GTE_MULTILINGUAL_BASE = "Alibaba-NLP/gte-multilingual-base"


class SentenceTransformerModel(BaseEmbeddingModel):
    """
    Embedding model that uses Sentence Transformers.
    """

    def __init__(
        self,
        model_name: str,
        normalize_embeddings: bool = True,
        trust_remote_code: bool = False,
    ):
        logger.debug(f"Initialized {model_name} Sentence Transformer")
        super().__init__(model_name=model_name)
        self.normalize_embeddings = normalize_embeddings
        self.model = SentenceTransformer(
            model_name, trust_remote_code=trust_remote_code
        )

    def generate_embeddings(self, texts: list[str]) -> list[Vector]:
        """
        Generate embeddings for a list of text inputs using Sentence Transformers.
        """
        embeddings = self.model.encode(
            texts, normalize_embeddings=self.normalize_embeddings
        )
        return [
            Vector(values=embedding, model_name=self.model_name)
            for embedding in embeddings
        ]
