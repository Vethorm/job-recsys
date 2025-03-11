from sentence_transformers import SentenceTransformer
import numpy as np
from loguru import logger

import torch

DEFAULT_MODEL = "all-MiniLM-L6-v2"

# Global model loaded on module import
MODEL = SentenceTransformer(DEFAULT_MODEL)

torch.classes.__path__ = []


def get_embeddings(items) -> list[np.ndarray]:
    """
    Generate embeddings for the given items using the globally loaded Sentence Transformer model.

    Args:
        items (str or list of str): A single text string or a list of text strings to encode.

    Returns:
        list or numpy.ndarray: The embeddings generated for the input items.
                                Returns a list if a single text string was provided.
    """
    # Ensure items is a list
    if isinstance(items, str):
        items = [items]

    logger.info(f"Generating embeddings for {len(items)} items")
    embeddings = MODEL.encode(items)
    logger.info("Done.")
    return embeddings


if __name__ == "__main__":
    # Example usage:
    sample_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Sentence transformers are great for generating embeddings.",
    ]
    embeddings = get_embeddings(sample_texts)

    print("Embeddings:")
    for text, emb in zip(sample_texts, embeddings):
        print(f"Text: {text}")
        print(f"Embedding: {emb}\n")
