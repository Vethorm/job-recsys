import numpy as np
from loguru import logger


def cosine_similarity(vec1, vec2):
    """
    Compute the cosine similarity between two vectors.

    Args:
        vec1 (array-like): First vector.
        vec2 (array-like): Second vector.

    Returns:
        float: Cosine similarity between vec1 and vec2.
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return np.dot(vec1, vec2) / (norm1 * norm2)


def search_jobs(resume_embedding, job_embeddings):
    """
    Perform vector search to rank jobs by relevance based on cosine similarity.

    Args:
        resume_embedding (array-like): The embedding vector for the resume.
        job_embeddings (list of array-like): A list of embedding vectors for job descriptions.

    Returns:
        list of tuples: A list of tuples (job_index, similarity) sorted by similarity in descending order.
    """
    logger.info("Running search")
    similarities = []
    for index, job_embedding in enumerate(job_embeddings):
        similarity = cosine_similarity(resume_embedding, job_embedding)
        similarities.append((index, similarity))

    # Sort jobs by similarity in descending order
    ranked_results = sorted(similarities, key=lambda x: x[1], reverse=True)
    logger.info("Done.")
    return ranked_results


if __name__ == "__main__":
    # Example usage:
    # For demonstration purposes, we'll generate random vectors.
    # In a real scenario, you'd get these embeddings from your embedding_generator module.
    resume_embedding = np.random.rand(384)
    job_embeddings = [np.random.rand(384) for _ in range(5)]

    ranked = search_jobs(resume_embedding, job_embeddings)
    for idx, sim in ranked:
        print(f"Job {idx} similarity: {sim:.4f}")
