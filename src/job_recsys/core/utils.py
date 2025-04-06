import hashlib


def hash_url(url: str) -> str:
    """Generate a hash for a URL.

    Args:
        url: URL to hash

    Returns:
        SHA-256 hash of the URL as a hex string
    """
    return hashlib.sha256(url.encode()).hexdigest()
