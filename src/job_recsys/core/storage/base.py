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
        """Save JSON content to storage.

        Args:
            key: Unique identifier where the content should be stored
            content: JSON-serializable content to store

        Returns:
            Key where the content was stored
        """
        pass

    @abstractmethod
    def get_json(self, key: str) -> dict[str, Any]:
        """Get JSON content from storage.

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
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
