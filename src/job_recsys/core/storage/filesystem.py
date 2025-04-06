import json
from pathlib import Path
from typing import Any

from loguru import logger

from job_recsys.core.storage.base import Storage


class FileSystemStorage(Storage):
    """File system implementation of storage.

    This class implements the Storage interface using the local filesystem.
    Content is stored as files with their keys represented as relative paths
    from a base directory.
    """

    def __init__(self, base_dir: str):
        """Initialize a filesystem storage instance.

        Args:
            base_dir: Base directory for all storage. Will be created if it doesn't exist.
        """
        self.base_dir = Path(base_dir).absolute()
        self._ensure_dir(self.base_dir)

    def _get_full_path(self, key: str) -> Path:
        """Convert a storage key to a full filesystem path.

        Args:
            key: Storage key to convert

        Returns:
            A Path object representing the full filesystem path
        """
        full_path = (self.base_dir / key).resolve()
        return full_path

    def _ensure_dir(self, path: Path) -> None:
        """Ensure that the specified directory exists.

        Args:
            path: Directory path to ensure exists
        """
        if not path.exists():
            logger.info(f"Path {path} did not exist, creating...")
            path.mkdir(parents=True, exist_ok=True)

    def save_json(self, key: str, content: dict[str, Any]) -> str:
        """Save JSON content to the filesystem.

        Args:
            key: Unique identifier where the content should be stored
            content: JSON-serializable content to store

        Returns:
            Key where the content was stored

        Note:
            Parent directories will be created if they don't exist.
        """
        full_path = self._get_full_path(key)
        self._ensure_dir(full_path.parent)

        with open(full_path, "w") as f:
            json.dump(content, f, indent=2)

        return key

    def get_json(self, key: str) -> dict[str, Any]:
        """Get JSON content from the filesystem.

        Args:
            key: Key of the content to retrieve

        Returns:
            Parsed JSON content

        Raises:
            KeyError: If the file does not exist
        """
        full_path = self._get_full_path(key)

        if not full_path.exists():
            raise KeyError(f"Key not found: {key}")

        with open(full_path, "r") as f:
            return json.load(f)

    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys under the given prefix.

        Args:
            prefix: Key prefix to list. If empty, lists all keys.

        Returns:
            List of keys matching the prefix

        Note:
            Keys are returned as relative paths from the base directory.
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
            key: Key to check

        Returns:
            True if content exists at the key, False otherwise
        """
        full_path = self._get_full_path(key)
        return full_path.exists() and full_path.is_file()
