from abc import ABC, abstractmethod
from typing import Any


class Storage(ABC):
    """Abstract storage class that defines the interface for all storage implementations.

    This class provides an abstract interface for key-value based storage systems
    that can be implemented for various backends like filesystem, databases,
    cloud storage, etc.
    """

    @abstractmethod
    def save_json(
        self,
        key: str,
        content: dict[str, Any],
    ) -> str:
        """Save JSON-serializable content to storage.

        Stores the provided content at the specified key in the storage system.

        Args:
            key: Unique identifier where the content should be stored
            content: JSON-serializable content to store

        Returns:
            Key where the content was stored
        """
        pass

    @abstractmethod
    def get_json(self, key: str) -> dict[str, Any]:
        """Retrieve JSON content from storage.

        Fetches and parses the JSON content associated with the given key.

        Args:
            key: Key of the content to retrieve

        Returns:
            Parsed JSON content

        Raises:
            KeyError: If the key does not exist in storage
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> list[str]:
        """List all keys in storage, optionally filtered by a prefix.

        Retrieves a list of keys stored in the storage system, with an optional
        prefix-based filtering mechanism.

        Args:
            prefix: Optional string to filter keys. Only keys starting with
                    this prefix will be returned. Defaults to an empty string
                    which returns all keys.

        Returns:
            A list of keys matching the optional prefix
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if a specific key exists in storage.

        Determines whether the given key is present in the storage system.

        Args:
            key: The key to check for existence

        Returns:
            Boolean indicating whether the key exists in storage
        """
        pass
