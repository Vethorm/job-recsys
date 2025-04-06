import json
from pathlib import Path
from typing import Any

from loguru import logger

from job_recsys.core.storage.base import Storage


class FileSystemStorage(Storage):
    """File system implementation of the Storage interface.

    Stores and retrieves JSON content using the local filesystem,
    with keys representing relative paths from a base directory.

    Attributes:
        base_dir (Path): Root directory for storing files
    """

    def __init__(self, base_dir: str):
        """Initialize a filesystem storage instance.

        Creates the base directory if it doesn't exist.

        Args:
            base_dir: Base directory path for storing files
        """
        self.base_dir = Path(base_dir).absolute()
        self._ensure_dir(self.base_dir)

    def _get_full_path(self, key: str) -> Path:
        """Convert a storage key to an absolute filesystem path.

        Resolves the key to a full, absolute path within the base directory.

        Args:
            key: Storage key to convert to a filesystem path

        Returns:
            Resolved absolute Path for the given key
        """
        full_path = (self.base_dir / key).resolve()
        return full_path

    def _ensure_dir(self, path: Path) -> None:
        """Create the specified directory if it doesn't exist.

        Args:
            path: Directory path to ensure exists
        """
        if not path.exists():
            logger.info(f"Path {path} did not exist, creating...")
            path.mkdir(parents=True, exist_ok=True)

    def save_json(self, key: str, content: dict[str, Any]) -> str:
        """Save JSON-serializable content to the filesystem.

        Writes the content to a file at the specified key location.
        Creates parent directories if they don't exist.

        Args:
            key: Unique identifier for the content's storage location
            content: JSON-serializable dictionary to store

        Returns:
            The key where the content was stored
        """
        full_path = self._get_full_path(key)
        self._ensure_dir(full_path.parent)

        with open(full_path, "w") as f:
            json.dump(content, f, indent=2)

        return key

    def get_json(self, key: str) -> dict[str, Any]:
        """Retrieve JSON content from the filesystem.

        Reads and parses JSON content from the file at the specified key.

        Args:
            key: Key identifying the content to retrieve

        Returns:
            Parsed JSON content as a dictionary

        Raises:
            KeyError: If no file exists at the specified key
        """
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise KeyError(f"Key not found: {key}")

        with open(full_path, "r") as f:
            return json.load(f)

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys under the given prefix.

        Finds all files under the specified prefix path, returning their
        relative paths from the base directory.

        Args:
            prefix: Key prefix to list. If empty, lists all keys.

        Returns:
            List of keys (relative paths) matching the prefix
        """
        prefix_path = self._get_full_path(prefix)

        if not prefix_path.exists():
            return []

        if prefix_path.is_file():
            return [str(prefix_path.relative_to(self.base_dir))]

        result = []
        for file_path in prefix_path.glob("**/*"):
            if file_path.is_file():
                result.append(str(file_path.relative_to(self.base_dir)))

        return result

    def exists(self, key: str) -> bool:
        """Check if content exists at the given key.

        Args:
            key: Key to check for existence

        Returns:
            True if content exists at the key, False otherwise
        """
        full_path = self._get_full_path(key)
        return full_path.exists() and full_path.is_file()
