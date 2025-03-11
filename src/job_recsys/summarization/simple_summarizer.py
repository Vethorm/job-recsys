import torch
from loguru import logger
from transformers import logging as transformers_logging, pipeline

transformers_logging.set_verbosity_error()

# Workaround for torch.classes path issue if needed
torch.classes.__path__ = []  # See: https://github.com/VikParuchuri/marker/issues/442#issuecomment-2636393925


def get_torch_device(force_cpu: bool = False) -> torch.device:
    """
    Determines the best available PyTorch device.

    Args:
        force_cpu (bool): If True, forces the use of CPU regardless of available accelerators.

    Returns:
        torch.device: The device to be used by PyTorch (e.g., 'cuda:0', 'mps', or 'cpu').
    """
    if force_cpu:
        logger.info("Force CPU is enabled. Using CPU.")
        return torch.device("cpu")

    if torch.cuda.is_available():
        num_gpus = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0)
        logger.info(
            f"CUDA is available. Using GPU 0: {device_name} (Total GPUs: {num_gpus})."
        )
        return torch.device("cuda:0")

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        logger.info("MPS is available. Using MPS device.")
        return torch.device("mps")

    logger.info("No GPU or MPS device found. Falling back to CPU.")
    return torch.device("cpu")


class SummarizationModels:
    PEGASUS_XSUM = "google/pegasus-xsum"
    PEGASUS_LARGE = "google/pegasus-large"
    BART_LARGE_CNN = "facebook/bart-large-cnn"


# Initialize the summarizer pipeline using the PEGASUS_XSUM model by default.
summarizer = pipeline(
    "summarization", model=SummarizationModels.PEGASUS_XSUM, device=get_torch_device()
)


def naive_chunk_text(text: str, max_tokens: int, token_factor: float) -> list:
    """
    Naively splits text into chunks based solely on the estimated token count.
    We estimate tokens by multiplying the number of characters by token_factor.
    The function computes a chunk size (in characters) as:
        chunk_size = int(max_tokens * token_factor)
    and then splits the text into segments of that size.

    Args:
        text (str): The input text.
        max_tokens (int): Maximum estimated tokens allowed per chunk.
        token_factor (float): Factor to estimate tokens from the character count.

    Returns:
        list: A list of text chunks.
    """
    chunk_size = int(max_tokens * token_factor)
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunk = text[i : i + chunk_size]
        chunks.append(chunk)

    if chunks:
        sizes = [len(chunk) for chunk in chunks]
        max_size = max(sizes)
        min_size = min(sizes)
        avg_size = sum(sizes) / len(sizes)
        logger.info(
            f"Naive chunk sizes (chars) - max: {max_size}, min: {min_size}, average: {avg_size:.2f}"
        )

    return chunks


def summarize_recursive(
    text: str, target_length: int = 350, max_tokens: int = 512, max_iterations: int = 5
) -> str:
    """
    Recursively summarizes the text by chunking it and summarizing each chunk.
    This process is repeated until the summary is short enough or max_iterations is reached.

    Args:
        text (str): Input text to summarize.
        target_length (int): Desired word count for the final summary.
        max_tokens (int): Maximum number of tokens (approximate) per chunk.
        max_iterations (int): Maximum number of summarization iterations.

    Returns:
        str: The final summarized text.
    """
    if not text.strip():
        raise ValueError("text cannot be empty or whitespace.")
    if len(text.split()) < 10:
        raise ValueError("Input text must contain at least 10 words.")

    iteration = 0
    current_text = text
    while len(current_text.split()) > target_length and iteration < max_iterations:
        logger.info(
            f"Iteration {iteration + 1}: Current text length is {len(current_text.split())} words, {len(current_text)} characters"
        )

        # Chunk the current text into pieces that fit into the model's context window
        chunks = naive_chunk_text(current_text, max_tokens, token_factor=3.0)
        logger.info(f"Created {len(chunks)} chunks for iteration {iteration + 1}")

        summaries = []
        for chunk in chunks:
            try:
                logger.info(f"Summarizing chunk of length {len(chunk)}")
                summary = summarizer(chunk, min_length=10, max_length=target_length)[0][
                    "summary_text"
                ]
                summaries.append(summary)
            except Exception as e:
                logger.warning(f"Failed to summarize a chunk: {e}")
                summaries.append("")  # Append empty string on failure

        # Combine the chunk summaries into one text for the next iteration
        current_text = " ".join(summaries)
        logger.info(
            f"After iteration {iteration + 1}, summary length is {len(current_text.split())} words"
        )
        iteration += 1

    if iteration == max_iterations and len(current_text.split()) > target_length:
        logger.warning(
            "Maximum iterations reached. Final summary may exceed the target length."
        )

    logger.info("Finished summarizing")
    return current_text
